/**
 * Màn hình tính năng test được bằng một object props thường.
 *
 * Không provider, không mock fetch, không `EventSource` giả — đó chính là lý do
 * ADR-0015 chọn *dữ liệu và callback* thay vì *hook và store*. Nếu một ngày bài
 * test này phải dựng provider, hợp đồng đã rò rỉ chi tiết cài đặt của shell.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { CatalogEntry } from "@/entities/feature";
import type { FeatureScreenProps } from "@/entities/feature-screen";
import { TestIntlProvider } from "@/lib/test-i18n";
import DetailScreen from "../frontend/DetailScreen";
import { project } from "../frontend/projection";

function props(overrides: Partial<FeatureScreenProps> = {}): FeatureScreenProps {
  return {
    // Qua `CatalogEntry.parse`, không phải một object literal: nó **kiểm** luôn
    // điều ADR-0079 điều 5 hứa — một catalog không khai `carScreen` vẫn parse
    // được và cho ba danh sách rỗng. Viết tay ba danh sách ấy sẽ làm fixture
    // xanh mà không chứng minh gì, và lệch đi lúc hình dạng khối đổi.
    feature: CatalogEntry.parse({
      id: "FT-000",
      name: "Tính năng mẫu",
      description: "Chỉ tồn tại trong scaffold.",
      status: "Draft",
      lastTested: "",
      frontend: { kind: "generic", componentKey: null },
      runtime: { stateDomains: ["motion"], events: [], frontendProjection: null },
    }),
    state: { motion: { socPct: 42 } },
    events: [],
    respond: vi.fn(),
    isLoading: false,
    slot: "inCarScreen",
    ...overrides,
  };
}

describe("DetailScreen mẫu", () => {
  it("hiện giá trị lấy qua projection", () => {
    render(
      <TestIntlProvider>
        <DetailScreen {...props()} />
      </TestIntlProvider>,
    );
    expect(screen.getByText("42%")).toBeInTheDocument();
  });

  it("miền chưa tới thì nói chưa có dữ liệu, không bịa số 0", () => {
    render(
      <TestIntlProvider>
        <DetailScreen {...props({ state: { motion: null } })} />
      </TestIntlProvider>,
    );
    expect(screen.getByText("chưa có dữ liệu")).toBeInTheDocument();
  });

  it("projection fail-closed khi trường sai kiểu", () => {
    expect(project({ motion: { socPct: "nhanh" } }).socPct).toBeNull();
    expect(project({}).socPct).toBeNull();
  });
});
