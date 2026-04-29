import { ImageResponse } from "next/og";

export const alt = "Mathingo — Procvičování matematiky ve stylu Duolinga";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#0073FF",
          color: "white",
          fontFamily:
            'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
        }}
      >
        <div
          style={{
            fontSize: 200,
            fontWeight: 900,
            letterSpacing: "-0.04em",
            lineHeight: 1,
          }}
        >
          Mathingo
        </div>
        <div
          style={{
            fontSize: 36,
            marginTop: 32,
            fontWeight: 600,
            opacity: 0.92,
          }}
        >
          Procvičování matematiky ve stylu Duolinga
        </div>
      </div>
    ),
    size,
  );
}
