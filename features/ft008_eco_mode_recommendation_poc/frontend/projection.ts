/**
 * Thu hẹp thứ nền tảng trao xuống thành thứ tính năng này đọc.
 *
 * Nền tảng biết *miền nào* — `motion`, `connectivity` — nhưng không biết
 * `socPct` nghĩa là gì với ai; biết được thì nó đã biết tên tính năng, và đó là
 * bất biến I3. Vì vậy `FeatureStateView` để ngỏ phần ruột và file này đóng lại
 * (ADR-0015). `runtime.frontendProjection` trỏ vào đây.
 *
 * **Fail-closed.** Trường vắng mặt hoặc sai kiểu trả về `null`, không trả về
 * một giá trị mặc định. Backend từ chối nói trên dữ liệu không tin được, và
 * màn hình chỉ nói đúng điều đó nếu "không biết" đến nơi dưới dạng "không
 * biết".
 *
 * **Ba thứ của gói `ft007_battery_status_recommendation` không có ở đây**, và
 * cả ba đi cùng luồng phản hồi mà `ba.md` §Phạm vi loại ra ngoài:
 * `answerFor()` (dựng thân request cho `respond`), `responseWindowSeconds`
 * (cửa sổ sáu giây), và `voiceLine` (POC không có kênh giọng nói — §9.1 Voice
 * UX là một tiêu đề rỗng, và `Bước 4` chỉ nói "hiển thị giao diện").
 *
 * `driving` cũng đi theo: nó phục vụ hai ràng buộc Driving-chỉ-Voice và
 * Parked-có-Answer-Card, cả hai đều ngoài phạm vi. `Bước 4` mô tả **một** cách
 * hiển thị và không đổi nó theo trạng thái xe.
 */
import type { FeatureStateView } from "@/entities/feature-screen";
import type { StreamEvent } from "@/entities/event";

export interface BatteryView {
  readonly socPct: number | null;
  readonly driveMode: string | null;
}

/** Một khuyến nghị đã tới màn hình, đọc từ luồng sự kiện của chính tính năng. */
export interface Recommendation {
  /** Định danh lượt xử lý. Màn hình so theo nó để biết đây là khuyến nghị mới. */
  readonly turnId: string;
  readonly candidateId: string;
  readonly message: string;
  readonly choices: readonly string[];
  /**
   * `BA-03` — hai nút có mặt nhưng không ấn được.
   *
   * Đọc từ payload chứ không hằng số hoá ở màn hình: đó là một điều `ba.md`
   * quy định và `service.public_result()` khai ra, nên nơi duy nhất giữ nó là
   * backend. Một `false` viết cứng ở đây sẽ là bản sao thứ hai của một luật.
   *
   * Mặc định `false` khi payload không nói: nút không bấm được là trạng thái
   * an toàn, nút bấm được mà không ai xử lý thì không.
   */
  readonly choicesInteractive: boolean;
  readonly occurredAt: string;
}

function pick<T>(
  state: FeatureStateView,
  domain: string,
  field: string,
  guard: (value: unknown) => value is T,
): T | null {
  const value = state[domain]?.[field];
  return guard(value) ? value : null;
}

const isNumber = (value: unknown): value is number => typeof value === "number";
const isBoolean = (value: unknown): value is boolean => typeof value === "boolean";
const isString = (value: unknown): value is string => typeof value === "string";

export function project(state: FeatureStateView): BatteryView {
  return {
    socPct: pick(state, "motion", "socPct", isNumber),
    driveMode: pick(state, "motion", "driveMode", isString),
  };
}

/**
 * Khuyến nghị mới nhất, hoặc `null` nếu chưa có.
 *
 * `events` đã được nền tảng lọc còn của riêng tính năng này và xếp mới nhất
 * trước, nên chỗ này chỉ cần lấy sự kiện `action` đầu tiên.
 */
export function latestRecommendation(
  events: readonly StreamEvent[],
): Recommendation | null {
  const action = events.find((event) => event.name === "action");
  if (!action || action.name !== "action") return null;

  const body = action.payload.payload;
  const choices = body.choices;
  const interactive = body.choicesInteractive;
  return {
    turnId: action.payload.turnId,
    candidateId: action.payload.candidateId,
    message: isString(body.message) ? body.message : "",
    choices: Array.isArray(choices) ? choices.filter(isString) : [],
    choicesInteractive: isBoolean(interactive) ? interactive : false,
    occurredAt: action.payload.occurredAt,
  };
}