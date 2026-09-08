/**
 * Màn hình chi tiết FT-007 — bốn ràng buộc của tài liệu BA chính thức.
 *
 * Test bằng một object props thường: không provider, không mock fetch, không
 * `EventSource` giả. Đó là điều ADR-0015 mua bằng việc trao *dữ liệu và
 * callback* thay vì *hook và store*, và bài test này là chỗ thấy được nó.
 *
 * Phủ `QC-06.1` · `QC-07.1` · `QC-07.2` · `QC-13.1` · `QC-22.1` · `QC-14.2`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CatalogEntry } from "@/entities/feature";
import type { FeatureScreenProps } from "@/entities/feature-screen";
import type { StreamEvent } from "@/entities/event";
import { TestIntlProvider } from "@/lib/test-i18n";
import DetailScreen from "../frontend/DetailScreen";

const TURN = "11111111-1111-4111-8111-111111111111";
const CANDIDATE = "c0ffee00c0ffee00c0ffee00c0ffee00";

function recommendation(): StreamEvent {
  return {
    name: "action",
    id: "1",
    payload: {
      turnId: TURN,
      candidateId: CANDIDATE,
      featureId: "FT-007",
      kind: "SUGGEST_ECO",
      payload: {
        voiceLine: "Pin còn 20%. Chuyển sang chế độ tiết kiệm nhé?",
        message: "Pin 20% · Chuyển chế độ tiết kiệm?",
        choices: ["Đồng ý", "Bỏ qua"],
        responseWindowSeconds: 6,
      },
      occurredAt: "2026-08-26T09:00:00Z",
    },
  };
}

function props(overrides: Partial<FeatureScreenProps> = {}): FeatureScreenProps {
  return {
    // Qua `CatalogEntry.parse`, không phải một object literal: nó **kiểm** luôn
    // điều ADR-0079 điều 5 hứa — một catalog không khai `carScreen` vẫn parse
    // được và cho ba danh sách rỗng. Viết tay ba danh sách ấy sẽ làm fixture
    // xanh mà không chứng minh gì, và lệch đi lúc hình dạng khối đổi.
    feature: CatalogEntry.parse({
      id: "FT-007",
      name: "Khuyến nghị chế độ vận hành theo trạng thái pin",
      description: "",
      status: "Active",
      lastTested: "2026-08-26",
      frontend: { kind: "custom", componentKey: "BatteryStatusRecommendationDetail" },
      runtime: {
        stateDomains: ["motion", "navigation", "interaction"],
        events: ["DRIVER_RESPONDED"],
        frontendProjection: "ft007",
      },
    }),
    state: { motion: { socPct: 20, vehicleInDrive: false, driveMode: "NORMAL" } },
    events: [recommendation()],
    respond: vi.fn().mockResolvedValue({ resolvedPlan: { message: "Đã chuyển sang Eco Mode." } }),
    isLoading: false,
    slot: "inCarScreen",
    ...overrides,
  };
}

const driving = { motion: { socPct: 20, vehicleInDrive: true, driveMode: "NORMAL" } };

function renderScreen(overrides: Partial<FeatureScreenProps> = {}) {
  return render(
    <TestIntlProvider>
      <DetailScreen {...props(overrides)} />
    </TestIntlProvider>,
  );
}

describe("FT-007 · màn hình chi tiết", () => {
  it("QC-07.1 · Parked thì hiện Answer Card với hai CTA tiếng Việt", () => {
    renderScreen();

    expect(screen.getByTestId("answer-card")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Chuyển sang Eco Mode" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Để sau" })).toBeInTheDocument();
    expect(screen.getByText("Pin 20% · Chuyển chế độ tiết kiệm?")).toBeInTheDocument();
  });

  it("QC-06.1 · Driving thì không có phần tử tương tác nào", () => {
    renderScreen({ state: driving });

    expect(screen.queryByTestId("answer-card")).not.toBeInTheDocument();
    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.getByRole("status")).toHaveTextContent("chỉ bằng giọng nói");
  });

  it("QC-13.1 · QC-22.1 · Parked chuyển sang Driving thì thẻ biến mất, không thu nhỏ", () => {
    const { rerender } = render(
      <TestIntlProvider>
        <DetailScreen {...props()} />
      </TestIntlProvider>,
    );
    expect(screen.getByTestId("answer-card")).toBeInTheDocument();

    rerender(
      <TestIntlProvider>
        <DetailScreen {...props({ state: driving })} />
      </TestIntlProvider>,
    );

    // Biến mất **hẳn**, cùng một lượt render với thay đổi trạng thái. Đo mốc
    // 100 ms trong một unit test là đo bộ đếm giờ của máy chạy test, không đo
    // hành vi; thứ đo được và đúng là: gỡ UI là một lần unmount đồng bộ, không
    // phải một hoạt ảnh, và không còn một thẻ nhỏ nào ở lại.
    expect(screen.queryByTestId("answer-card")).not.toBeInTheDocument();
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });

  it("QC-07.2 · chạm CTA gửi đúng một câu trả lời, kênh touch", async () => {
    const user = userEvent.setup();
    const respond = vi.fn().mockResolvedValue({ resolvedPlan: { message: "Đã chuyển sang Eco Mode." } });
    renderScreen({ respond });

    await user.click(screen.getByRole("button", { name: "Chuyển sang Eco Mode" }));

    expect(respond).toHaveBeenCalledTimes(1);
    expect(respond.mock.calls[0]?.[0]).toMatchObject({
      candidateId: CANDIDATE,
      outcome: "accept",
      channel: "touch",
    });
    expect(await screen.findByText("Đã chuyển sang Eco Mode.")).toBeInTheDocument();
  });

  it("QC-07.2 · chỉ báo thành công khi backend nói thành công", async () => {
    const user = userEvent.setup();
    const respond = vi.fn().mockRejectedValue(new Error("cổng xe từ chối"));
    renderScreen({ respond });

    await user.click(screen.getByRole("button", { name: "Chuyển sang Eco Mode" }));

    expect(await screen.findByText("Chưa chuyển được sang Eco Mode.")).toBeInTheDocument();
  });
});

describe("FT-007 · cửa sổ trả lời", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("QC-14.2 · 6 giây không trả lời thì tương tác kết thúc", async () => {
    const respond = vi.fn().mockResolvedValue({});
    renderScreen({ respond });
    expect(screen.getByTestId("answer-card")).toBeInTheDocument();

    // Không dùng `waitFor` ở đây: nó tự đặt hẹn giờ, và với đồng hồ giả thì
    // hẹn giờ đó không bao giờ tới — bài test treo cho tới lúc hết hạn vì lý do
    // không liên quan gì tới thứ đang kiểm. `act` bất đồng bộ đã xả hết
    // microtask, nên khẳng định thẳng là đủ và đọc rõ hơn.
    await act(async () => {
      vi.advanceTimersByTime(6_000);
    });

    expect(screen.queryByTestId("answer-card")).not.toBeInTheDocument();
    expect(respond.mock.calls[0]?.[0]).toMatchObject({ outcome: "timeout", channel: "none" });
  });
});
