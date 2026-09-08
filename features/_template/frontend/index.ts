/**
 * Điểm vào UI của tính năng. `generate_frontend_registry.py` sinh ra một
 * dynamic import trỏ vào đúng đường dẫn `@features/<package>/frontend`, nên
 * export mặc định ở đây là thứ nền tảng mount.
 */
export { default } from "./DetailScreen";
