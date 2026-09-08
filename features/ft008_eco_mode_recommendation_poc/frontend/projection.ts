/**
 * Thu hẹp thứ nền tảng trao xuống thành thứ tính năng này đọc.
 *
 * Nền tảng biết *miền nào* — `motion`, `navigation`, `interaction` — nhưng
 * không biết `socPct` nghĩa là gì với ai; biết được thì nó đã biết tên tính
 * năng, và đó là bất biến I3. Vì vậy `FeatureStateView` để ngỏ phần ruột và
 * file này đóng lại (ADR-0015). `runtime.frontendProjection` trỏ vào đây.
 *
 * **Fail-closed.** Trường vắng mặt hoặc sai kiểu trả về `null`, không trả về
 * một giá trị mặc định. `E01` cho phép trợ lý từ chối nói trên dữ liệu không
 * tin được, và nó chỉ từ chối được nếu "không biết" đến nơi dưới dạng "không
 * biết" — đúng bài học của [C022](../../../docs/devlog/sprint-04-goi-tinh-nang-tu-chua/log.md).
 */
import type { FeatureStateView } from "@/entities/feature-screen";
import type { StreamEvent } from "@/entities/event";

export interface BatteryView {
  readonly socPct: number | null;
  /** `null` = chưa biết xe đang lái hay đang đỗ, khác hẳn "đang đỗ". */
  readonly driving: boolean | null;
  readonly driveMode: string | null;
}

/** Một đề nghị đã tới tài xế, đọc từ luồng sự kiện của chính tính năng. */
export interface Recommendation {
  /** Định danh lượt xử lý. */
  readonly turnId: string;
  /** Định danh đề cử — thứ `answerFor` gửi ngược lại. */
  readonly candidateId: string;
  readonly voiceLine: string;
  readonly message: string;
  readonly choices: readonly string[];
  readonly responseWindowSeconds: number;
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
    driving: pick(state, "motion", "vehicleInDrive", isBoolean),
    driveMode: pick(state, "motion", "driveMode", isString),
  };
}

/**
 * Đề nghị mới nhất, hoặc `null` nếu chưa có.
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
  const window = body.responseWindowSeconds;
  return {
    turnId: action.payload.turnId,
    candidateId: action.payload.candidateId,
    voiceLine: isString(body.voiceLine) ? body.voiceLine : "",
    message: isString(body.message) ? body.message : "",
    choices: Array.isArray(choices) ? choices.filter(isString) : [],
    // 6 giây là hằng số của `AC-14`, không phải một mặc định tuỳ tiện: nếu
    // payload không nói, cửa sổ vẫn phải đóng đúng lúc tài liệu bảo nó đóng.
    responseWindowSeconds: isNumber(window) ? window : 6,
    occurredAt: action.payload.occurredAt,
  };
}

/**
 * Thân request cho `respond`, có kiểu — nền tảng không type hẹp chỗ này được.
 *
 * `candidateId` đi thẳng từ `ActionPayload` mà nền tảng phát ra. Trước P19 chỗ
 * này gửi `runId` lấy từ `turnId` — một cây cầu tạm, vì không gì trong hệ thống
 * sinh ra `runId` ([`DEBT-031`](../../../docs/devlog/debts-ledger.md)).
 */
export function answerFor(
  recommendation: Recommendation,
  outcome: "accept" | "reject" | "snooze" | "timeout",
  respondedAfterSeconds: number,
): Record<string, unknown> {
  return {
    candidateId: recommendation.candidateId,
    outcome,
    // `touch` chỉ hợp lệ khi xe đang đỗ (`AC-07`); màn hình gọi hàm này đúng
    // trong nhánh đó, và cửa sổ hết giờ thì không có kênh nào trả lời cả.
    channel: outcome === "timeout" ? "none" : "touch",
    respondedAfterSeconds,
  };
}
