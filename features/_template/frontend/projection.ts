/**
 * Thu hẹp trạng thái nền tảng trao xuống thành thứ tính năng này thật sự đọc.
 *
 * Đây là chỗ **duy nhất** một tính năng tự khẳng định kiểu. Nền tảng biết *miền
 * nào* (`runtime.stateDomains`), không biết *trường nào có nghĩa gì với ai* —
 * biết được thì nó đã biết tên tính năng, và đó là bất biến I3. Vì vậy
 * `FeatureStateView` để ngỏ phần ruột, và file này đóng lại (ADR-0015).
 *
 * `runtime.frontendProjection` trong `feature.yaml` trỏ tới đúng file này.
 *
 * Fail-closed: một trường vắng mặt hoặc sai kiểu trả về `null`, không trả về
 * một giá trị mặc định trông như số đo. Màn hình hiện "chưa có dữ liệu" thì
 * đúng; hiện `0%` thì là bịa.
 */
import type { FeatureStateView } from "@/entities/feature-screen";

export interface TemplateView {
  /** `null` = miền chưa tới, hoặc trường không có trong đó. */
  readonly socPct: number | null;
}

function numberAt(
  state: FeatureStateView,
  domain: string,
  field: string,
): number | null {
  const value = state[domain]?.[field];
  return typeof value === "number" ? value : null;
}

export function project(state: FeatureStateView): TemplateView {
  return { socPct: numberAt(state, "motion", "socPct") };
}
