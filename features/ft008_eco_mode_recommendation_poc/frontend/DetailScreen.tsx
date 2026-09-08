"use client";

/**
 * Màn hình của gói POC.
 *
 * Nền tảng mount **cùng component này ba lần**, một lần cho mỗi panel của
 * workspace (`props.slot`) — ba mount **độc lập**, không chia sẻ state cho
 * nhau. Cả ba đọc từ `state` và `events`.
 *
 * Nó **không quyết định** khi nào nói. `service.py` quyết định; màn hình hiển
 * thị thứ backend đã đưa.
 *
 * ── Khác gì màn hình của `ft007_battery_status_recommendation` ────────────
 *
 * Ở đó bốn ràng buộc tài liệu sống trong màn hình: Driving chỉ Voice, Parked có
 * Answer Card với hai CTA bấm được, Parked→Driving gỡ UI trong 100 ms, và cửa
 * sổ trả lời sáu giây. Cả bốn đều ngoài phạm vi của `ba.md` gói này, nên màn
 * hình này **không có** `useState`, `useEffect`, `setTimeout`, `respond`, và
 * không phân nhánh theo trạng thái xe.
 *
 * Cái còn lại là một ràng buộc duy nhất, `BA-03`: hiển thị câu hỏi và hai nút
 * xác nhận **ở trạng thái không thao tác được**.
 *
 * `disabled` chứ không phải vắng mặt, và khác biệt ấy là điều `Bước 4` yêu
 * cầu: hai nút phải **có mặt** để người xem thấy hình dạng của tương tác sẽ có,
 * và phải **không ấn được** vì chưa có gì phía sau chúng. Ẩn chúng đi là dựng
 * một màn hình khác với màn hình tài liệu mô tả.
 */
import { useMemo } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/layout/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import type { FeatureScreenProps } from "@/entities/feature-screen";
import { latestRecommendation, project } from "./projection";
import type { BatteryView, Recommendation } from "./projection";

export default function DetailScreen({ slot, state, events, isLoading }: FeatureScreenProps) {
  const t = useTranslations("ft008.detailScreen");
  const view = useMemo(() => project(state), [state]);
  const recommendation = useMemo(() => latestRecommendation(events), [events]);

  if (isLoading) return <Skeleton className="h-40" />;

  if (slot === "input") return <InputPanel view={view} />;
  if (slot === "output") return <OutputPanel recommendation={recommendation} />;

  return (
    <div className="space-y-4 p-3">
      <h2 className="text-sm font-semibold">{t("batteryStatusTitle")}</h2>
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

      {recommendation && <RecommendationCard recommendation={recommendation} />}
    </div>
  );
}

/**
 * `Bước 4` — câu hỏi và hai nút xác nhận cảm ứng, không ấn được.
 *
 * Hình thẻ kế thừa từ màn hình của gói kia để hai bề mặt trông như một hệ
 * thống. Khác một điểm cần nói rõ: ở đó hình thẻ là **hợp đồng nghiệp vụ** —
 * tài liệu BA gọi đúng thứ này là "Answer Card". `ba.md` của gói này để trống
 * §9.2 Visual UX và không đặt tên cho thành phần nào, nên ở đây hình thẻ là
 * một lựa chọn trình bày, không phải một yêu cầu. Nếu §9.2 được điền và nói
 * khác, chỗ này đổi theo mà không ảnh hưởng gì tới backend.
 */
function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const t = useTranslations("ft008.detailScreen");
  return (
    <Card data-testid="recommendation-card">
      <CardHeader>
        <CardTitle className="text-base">{t("recommendationTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm">{recommendation.message}</p>
        <div className="flex gap-2">
          {recommendation.choices.map((choice, index) => (
            <Button
              key={choice}
              size="sm"
              variant={index === 0 ? "default" : "outline"}
              disabled={!recommendation.choicesInteractive}
              // `disabled` một mình đủ chặn chuột và bàn phím, nhưng trình đọc
              // màn hình thông báo một nút `disabled` bằng cách bỏ qua nó. Nút
              // ở đây phải được **nghe thấy** rồi mới biết là chưa dùng được —
              // đó là điều `Bước 4` mô tả, và `aria-disabled` là cách nói ra.
              aria-disabled={!recommendation.choicesInteractive}
            >
              {choice}
            </Button>
          ))}
        </div>
        {/* Nói ra một lần, cho người xem demo. Không có dòng này thì hai nút
            xám trông như một lỗi giao diện thay vì một trạng thái được thiết
            kế. */}
        {!recommendation.choicesInteractive && (
          <p role="status" className="text-muted-foreground text-xs">
            {t("notInteractiveNote")}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/** Panel `input` — thứ tính năng nhận vào ở lượt hiện tại. Chỉ hiển thị. */
function InputPanel({ view }: { view: BatteryView }) {
  const t = useTranslations("ft008.detailScreen");
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
      </div>
    </div>
  );
}

/** Panel `output` — nội dung khuyến nghị hiện tại, đọc từ `events` dùng chung. */
function OutputPanel({ recommendation }: { recommendation: Recommendation | null }) {
  const t = useTranslations("ft008.detailScreen");
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
      <p className="text-sm">{recommendation.message}</p>
    </div>
  );
}