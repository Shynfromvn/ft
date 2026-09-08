/**
 * Màn hình chi tiết của gói POC — một ràng buộc, `BA-03`.
 *
 * Test bằng một object props thường: không provider, không mock fetch, không
 * `EventSource` giả. Đó là điều ADR-0015 mua bằng việc trao *dữ liệu và
 * callback* thay vì *hook và store*, và bài test này là chỗ thấy được nó.
 *
 * **Sáu bài của `ft007_battery_status_recommendation` không có ở đây**, và cả
 * sáu đi cùng ràng buộc chúng kiểm: Parked hiện Answer Card, Driving không có
 * phần tử tương tác, Parked→Driving gỡ UI, chạm CTA gửi câu trả lời, chỉ báo
 * thành công khi backend nói thành công, và cửa sổ sáu giây. `ba.md` của gói
 * này đưa cả bốn ràng buộc ấy ra ngoài phạm vi.
 *
 * Không có `vi.useFakeTimers()` ở đây, và đó là một điều đáng nói chứ không
 * phải một chỗ bỏ sót: màn hình không đặt hẹn giờ nào, nên không có gì để tua.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CatalogEntry } from "@/entities/feature";
import type { FeatureScreenProps } from "@/entities/feature-screen";
import type { StreamEvent } from "@/entities/event";
import { TestIntlProvider } from "@/lib/test-i18n";
import DetailScreen from "../frontend/DetailScreen";

const TURN = "11111111-1111-4111-8111-111111111111";
const CANDIDATE = "c0ffee00c0ffee00c0ffee00c0ffee00";

/** Câu nguyên văn `ba.md` `Bước 3` — cùng chuỗi `test_service.py` ghim ở backend. */
const MESSAGE =
  "Pin còn 20%. Chuyển sang Eco Mode có thể giúp tiết kiệm pin hơn. " +
  "Bạn có đồng ý chuyển không?";

function recommendation(overrides: Record<string, unknown> = {}): StreamEvent {
  return {
    name: "action",
    id: "1",
    payload: {
      turnId: TURN,
      candidateId: CANDIDATE,
      featureId: "FT-008",
      kind: "SUGGEST_ECO",
      payload: {
        message: MESSAGE,
        choices: ["Đồng ý", "Không đồng ý"],
        choicesInteractive: false,
        ...overrides,
      },
      occurredAt: "2026-09-08T09:00:00Z",
    },
  };
}

function props(overrides: Partial<FeatureScreenProps> = {}): FeatureScreenProps {
  return {
    // Qua `CatalogEntry.parse`, không phải một object literal: nó **kiểm** luôn
    // điều ADR-0079 điều 5 hứa — một catalog không khai `carScreen` vẫn parse
    // được và cho ba danh sách rỗng.
    feature: CatalogEntry.parse({
      id: "FT-008",
      name: "Khuyến nghị chuyển Eco Mode khi pin thấp (POC)",
      description: "",
      status: "Draft",
      lastTested: "",
      frontend: { kind: "custom", componentKey: "EcoModeRecommendationPocDetail" },
      runtime: {
        // Hai miền, khớp `runtime.stateDomains` của `feature.yaml`. Danh sách
        // `events` rỗng vì không sự kiện nào định tuyến vào tính năng này.
        stateDomains: ["motion", "connectivity"],
        events: [],
        frontendProjection: "ft008",
      },
    }),
    state: { motion: { socPct: 20, driveMode: "NORMAL" } },
    events: [recommendation()],
    isLoading: false,
    slot: "inCarScreen",
    ...overrides,
  };
}

function renderScreen(overrides: Partial<FeatureScreenProps> = {}) {
  return render(
    <TestIntlProvider>
      <DetailScreen {...props(overrides)} />
    </TestIntlProvider>,
  );
}

describe("POC · màn hình chi tiết", () => {
  it("Bước 4 · hiện câu hỏi và hai nút xác nhận", () => {
    renderScreen();

    expect(screen.getByTestId("recommendation-card")).toBeInTheDocument();
    expect(screen.getByText(MESSAGE)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Đồng ý" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Không đồng ý" })).toBeInTheDocument();
  });

  it("BA-03 · hai nút có mặt nhưng không ấn được", async () => {
    const user = userEvent.setup();
    renderScreen();

    const accept = screen.getByRole("button", { name: "Đồng ý" });
    const decline = screen.getByRole("button", { name: "Không đồng ý" });

    // Ba khẳng định, ba người đọc khác nhau. `toBeDisabled` là điều chuột thấy;
    // `aria-disabled` là điều trình đọc màn hình nghe được — một nút `disabled`
    // trơn bị bỏ qua khi duyệt, mà `Bước 4` đòi nút phải **có mặt**.
    expect(accept).toBeDisabled();
    expect(decline).toBeDisabled();
    expect(accept).toHaveAttribute("aria-disabled", "true");

    // Và điều người dùng thấy: bấm không làm gì cả. Nếu ai đó gỡ `disabled`
    // nhưng quên gắn handler, hai khẳng định trên đỏ trước — bài này là lớp
    // cuối, cho trường hợp ngược lại.
    await user.click(accept);
    expect(screen.getByTestId("recommendation-card")).toBeInTheDocument();
  });

  it("BA-03 · nói ra một lần rằng nút chưa dùng được", () => {
    renderScreen();

    // Không có dòng này thì hai nút xám trông như một lỗi giao diện thay vì
    // một trạng thái được thiết kế — và người xem demo là người đọc nó.
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("trạng thái tương tác đọc từ payload, không viết cứng ở màn hình", async () => {
    // Ghim đường dẫn của luật, không phải giá trị của nó. `BA-03` sống ở
    // `service.public_result()`; nếu ai đó hằng số hoá `disabled` ở màn hình,
    // bài này đỏ vì payload nói `true` mà nút vẫn xám.
    renderScreen({ events: [recommendation({ choicesInteractive: true })] });

    expect(screen.getByRole("button", { name: "Đồng ý" })).toBeEnabled();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("chưa có khuyến nghị nào thì không có thẻ, không có nút", () => {
    renderScreen({ events: [] });

    expect(screen.queryByTestId("recommendation-card")).not.toBeInTheDocument();
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  it("payload thiếu trường thì fail-closed, không dựng giá trị mặc định", () => {
    // `choicesInteractive` vắng mặt đọc thành `false`. Chiều mặc định là điều
    // đáng ghim: nút không bấm được là trạng thái an toàn, nút bấm được mà
    // không ai xử lý thì không.
    renderScreen({ events: [recommendation({ choicesInteractive: undefined })] });

    expect(screen.getByRole("button", { name: "Đồng ý" })).toBeDisabled();
  });

  it("mức pin và chế độ lái hiển thị từ state", () => {
    renderScreen();

    expect(screen.getByText("20%")).toBeInTheDocument();
    expect(screen.getByText("NORMAL")).toBeInTheDocument();
  });

  it("miền motion chưa tới thì hiện 'không biết', không hiện 0%", () => {
    // Khác nhau giữa "chưa nhận được số đo" và "pin cạn" là khác biệt mà cả
    // `runtime.py` lẫn `projection.ts` đều fail-closed để giữ. Một màn hình
    // hiện `0%` ở đây sẽ báo động về một chuyện chưa ai quan sát được.
    renderScreen({ state: {} });

    expect(screen.queryByText("0%")).not.toBeInTheDocument();
  });
});

describe("POC · ba panel", () => {
  it("panel input chỉ hiển thị, không có nút", () => {
    renderScreen({ slot: "input" });

    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.getByText("20%")).toBeInTheDocument();
  });

  it("panel output hiện nội dung khuyến nghị", () => {
    renderScreen({ slot: "output" });

    expect(screen.getByText(MESSAGE)).toBeInTheDocument();
  });

  it("panel output chưa có gì thì hiện trạng thái rỗng", () => {
    renderScreen({ slot: "output", events: [] });

    expect(screen.queryByText(MESSAGE)).not.toBeInTheDocument();
  });
});