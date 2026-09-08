"use client";

/**
 * Màn hình của FT-007 — consumer thật đầu tiên của ADR-0015 và ADR-0017.
 *
 * Nền tảng mount **cùng component này ba lần**, một lần cho mỗi panel của
 * workspace (`props.slot`) — ba mount **độc lập**, không chia sẻ state cho
 * nhau. Chỉ mount `slot="inCarScreen"` chạy engine tương tác thật (hẹn giờ,
 * `respond`); `input`/`output` là hai bản hiển thị thuần, đọc từ `state` và
 * `events` — hai prop dùng chung cho cả ba mount, khác với `phase`/`status`
 * vốn là state cục bộ của riêng mount đang tương tác.
 *
 * Nó **không quyết định** khi nào nói. `service.py` quyết định; màn hình hiển
 * thị thứ backend đã đưa và gửi lại câu trả lời của tài xế. Mọi chỗ code lệch
 * tài liệu phát hiện lúc dựng màn hình này đi vào `DEBT-020`, không đi vào một
 * bản vá ở tầng giao diện.
 *
 * Bốn ràng buộc của tài liệu, và chỗ thực hiện từng cái — cả bốn chỉ áp dụng
 * cho `slot="inCarScreen"`, đây là màn hình thật trên xe:
 *
 * | | |
 * |---|---|
 * | `AC-06` Driving chỉ Voice | `driving === true` → không render phần tử tương tác nào |
 * | `AC-07` Parked có Answer Card, hai CTA tiếng Việt | `<AnswerCard>` |
 * | `AC-13`/`NFR-06` Parked→Driving gỡ UI ≤ 100 ms, không thu nhỏ | thẻ **unmount**, không animate, không thu nhỏ |
 * | `AC-14` 6 giây không trả lời thì kết thúc | `useEffect` + `setTimeout` theo `responseWindowSeconds` |
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/layout/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import type { FeatureScreenProps } from "@/entities/feature-screen";
import { answerFor, latestRecommendation, project } from "./projection";
import type { BatteryView, Recommendation } from "./projection";

type Phase = "waiting" | "answering" | "done";

export default function DetailScreen({ slot, state, events, respond, isLoading }: FeatureScreenProps) {
  const t = useTranslations("ft007.detailScreen");
  const view = useMemo(() => project(state), [state]);
  const recommendation = useMemo(() => latestRecommendation(events), [events]);

  const [phase, setPhase] = useState<Phase>("waiting");
  const [status, setStatus] = useState<string | null>(null);
  const [lastTurn, setLastTurn] = useState<string | null>(null);
  const openedAt = useRef<number | null>(null);

  // Một đề nghị mới mở lại cửa sổ. So theo `turnId` chứ không theo tham chiếu:
  // luồng sự kiện dựng lại mảng mỗi lần có frame, nên so tham chiếu sẽ reset
  // cửa sổ liên tục và tài xế không bao giờ hết giờ.
  //
  // Điều chỉnh **state** lúc render là cách React khuyến nghị cho việc này; điều
  // chỉnh một `ref` thì không, và `react-hooks/refs` nói đúng — một ref sửa
  // giữa render không có gì bảo đảm về thứ tự với lần render mà nó ảnh hưởng.
  if (recommendation && lastTurn !== recommendation.turnId) {
    setLastTurn(recommendation.turnId);
    setPhase("waiting");
    setStatus(null);
  }

  const finish = useCallback(
    async (outcome: "accept" | "reject" | "snooze" | "timeout") => {
      if (!recommendation) return;
      setPhase("answering");
      const after = openedAt.current === null ? 0 : (Date.now() - openedAt.current) / 1000;
      try {
        const result = await respond(answerFor(recommendation, outcome, after));
        const plan = result.resolvedPlan;
        const line =
          plan && typeof plan === "object" && "message" in plan
            ? String((plan as Record<string, unknown>).message)
            : null;
        // Chỉ báo thành công khi backend nói thành công (mục 9.2 §3 của tài
        // liệu). Không suy ra từ việc nút được bấm — bộ điều khiển có quyền từ
        // chối, và báo thành công giả tốn niềm tin vào cả trợ lý.
        setStatus(line ?? t("answeredDefault"));
      } catch {
        setStatus(t("answerFailed"));
      }
      setPhase("done");
    },
    [recommendation, respond, t],
  );

  // `AC-14`: hết 6 giây mà không có phản hồi nào được hỗ trợ thì tương tác kết
  // thúc và chế độ vận hành giữ nguyên. Chặn bằng `slot` trước tiên: ba mount
  // độc lập cùng đọc `recommendation` từ `events` dùng chung, nên không chặn
  // ở đây thì cả ba đặt hẹn giờ riêng và cả ba cùng gọi `respond` khi hết giờ.
  const live =
    slot === "inCarScreen" && recommendation !== null && phase === "waiting" && view.driving === false;
  useEffect(() => {
    if (!live || !recommendation) return;
    openedAt.current = Date.now();
    const timer = setTimeout(
      () => void finish("timeout"),
      recommendation.responseWindowSeconds * 1000,
    );
    return () => clearTimeout(timer);
  }, [live, recommendation, finish]);

  if (isLoading) return <Skeleton className="h-40" />;

  if (slot === "input") return <InputPanel view={view} />;
  if (slot === "output") return <OutputPanel recommendation={recommendation} />;

  return (
    <div className="space-y-4 p-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">{t("batteryStatusTitle")}</h2>
        <Badge variant="outline" className="font-mono">
          {view.driving === null
            ? t("unknownBadge")
            : view.driving
              ? t("drivingBadge")
              : t("parkedBadge")}
        </Badge>
      </div>
      <div className="space-y-1 text-sm">
        <p>
          {t("socLabel")}:{" "}
          <span className="font-mono">
            {view.socPct === null ? t("noData") : `${view.socPct}%`}
          </span>
        </p>
        <p className="text-muted-foreground">
          {t("driveModeLabel")}: <span className="font-mono">{view.driveMode ?? t("noData")}</span>
        </p>
      </div>

      {/* `AC-06`: đang lái thì KHÔNG có popup, Answer Card, Toast, Mascot, CTA,
          text chi tiết, biểu mẫu, danh sách hay UI chạm nào. Một dòng trạng
          thái không tương tác cho người xem demo là tất cả những gì còn lại. */}
      {view.driving === true && (
        <p role="status" className="text-muted-foreground text-xs">
          {t("drivingStatus")}
        </p>
      )}

      {view.driving === false && recommendation && phase !== "done" && (
        <AnswerCard
          recommendation={recommendation}
          busy={phase === "answering"}
          onAccept={() => void finish("accept")}
          onDefer={() => void finish("snooze")}
        />
      )}

      {status && (
        <p role="status" className="text-sm">
          {status}
        </p>
      )}
    </div>
  );
}

/**
 * `AC-07`: mức pin, gợi ý Eco, lợi ích ngắn, và hai CTA tiếng Việt.
 *
 * Tách thành component riêng vì `AC-13` nói về **thẻ này**: khi xe chuyển sang
 * Driving nó phải biến mất hẳn, không thu nhỏ. Một cây con riêng làm điều đó
 * thành một lần unmount thay vì một chuỗi class có điều kiện.
 *
 * Nơi duy nhất trong màn hình này còn dùng `Card` — có chủ đích, không phải
 * quên: tài liệu BA chính thức gọi đúng thứ này là "Answer Card"
 * (`glossary.md`, thuật ngữ `answerCard`), nên hình dạng thẻ là một phần của
 * hợp đồng nghiệp vụ, không phải lựa chọn trang trí.
 */
function AnswerCard({
  recommendation,
  busy,
  onAccept,
  onDefer,
}: {
  recommendation: Recommendation;
  busy: boolean;
  onAccept: () => void;
  onDefer: () => void;
}) {
  const t = useTranslations("ft007.detailScreen");
  return (
    <Card data-testid="answer-card">
      <CardHeader>
        <CardTitle className="text-base">{t("answerCardTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm">{recommendation.message}</p>
        <p className="text-muted-foreground text-xs">{t("answerCardBenefit")}</p>
        <div className="flex gap-2">
          <Button size="sm" disabled={busy} onClick={onAccept}>
            {t("acceptButton")}
          </Button>
          <Button size="sm" variant="outline" disabled={busy} onClick={onDefer}>
            {t("deferButton")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/** Panel `input` — thứ tính năng nhận vào ở lượt hiện tại. Chỉ hiển thị, không tương tác. */
function InputPanel({ view }: { view: BatteryView }) {
  const t = useTranslations("ft007.detailScreen");
  return (
    <div className="space-y-3 p-3">
      <h2 className="text-sm font-semibold">{t("inputTitle")}</h2>
      <div className="space-y-1 text-sm">
        <p>
          {t("socLabel")}:{" "}
          <span className="font-mono">
            {view.socPct === null ? t("noData") : `${view.socPct}%`}
          </span>
        </p>
        <p className="text-muted-foreground">
          {t("driveModeLabel")}: <span className="font-mono">{view.driveMode ?? t("noData")}</span>
        </p>
        <p className="text-muted-foreground">
          {t("drivingLabel")}:{" "}
          <span className="font-mono">
            {view.driving === null ? t("noData") : view.driving ? t("drivingYes") : t("drivingNo")}
          </span>
        </p>
      </div>
    </div>
  );
}

/**
 * Panel `output` — nội dung khuyến nghị hiện tại, đọc từ `events` dùng chung.
 *
 * Không hiện `status` (câu xác nhận sau khi bấm CTA): đó là state cục bộ của
 * mount `inCarScreen`, nơi CTA thật sự tồn tại — một mount khác của cùng
 * component không thấy được nó (xem ghi chú lệch trong plan P16).
 */
function OutputPanel({ recommendation }: { recommendation: Recommendation | null }) {
  const t = useTranslations("ft007.detailScreen");
  if (!recommendation) {
    return (
      <div className="p-3">
        <EmptyState title={t("outputEmptyTitle")} description={t("outputEmptyDescription")} />
      </div>
    );
  }
  return (
    <div className="space-y-3 p-3">
      <h2 className="text-sm font-semibold">{t("outputTitle")}</h2>
      <div className="space-y-1 text-sm">
        <p>{recommendation.message}</p>
        <p className="text-muted-foreground text-xs">
          {t("responseWindowLabel")}:{" "}
          <span className="font-mono">{recommendation.responseWindowSeconds}s</span>
        </p>
      </div>
    </div>
  );
}
