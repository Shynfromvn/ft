"use client";

/**
 * Màn hình chi tiết mẫu — chỗ để thay, không phải chỗ để giữ.
 *
 * Tồn tại để một tính năng mới có **ô sẵn** cho phần giao diện. Không có nó,
 * `make feature-new` dựng một tính năng không có chỗ nào đặt UI, và người viết
 * quay về `frontend/src/` — đúng thứ bất biến I1 cấm, vì một lý do rất người:
 * chỗ trống thì người ta điền, chỗ không có thì người ta đi nơi khác.
 *
 * Nó cũng là **consumer thứ hai** của hợp đồng props (ADR-0015), nên hợp đồng
 * không thể vừa khít đúng một tính năng.
 */
import { useTranslations } from "next-intl";
import type { FeatureScreenProps } from "@/entities/feature-screen";
import { project } from "./projection";

export default function DetailScreen({
  feature,
  state,
  events,
  isLoading,
}: FeatureScreenProps) {
  const t = useTranslations("featureTemplate.detailScreen");
  const view = project(state);

  if (isLoading) {
    return <p className="text-muted-foreground text-sm">{t("loading")}</p>;
  }

  return (
    <section className="space-y-3" aria-label={t("screenLabel", { featureId: feature.id })}>
      <p className="text-sm">
        {t("speedLabel")}:{" "}
        <span className="font-mono">
          {view.socPct === null ? t("noData") : `${view.socPct}%`}
        </span>
      </p>
      <p className="text-muted-foreground text-xs">{t("eventCount", { count: events.length })}</p>
    </section>
  );
}
