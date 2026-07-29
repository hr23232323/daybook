import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";

const WIDTH = 1080;
const HEIGHT = 1080;
const SOURCE_WIDTH = 1600;
const SOURCE_HEIGHT = 1000;
const BASE_SCALE = HEIGHT / SOURCE_HEIGHT;
const INK = "#17272c";
const CREAM = "#f7f3eb";
const ORANGE = "#d28b55";

type Keyframe = {
  frame: number;
  focusX: number;
  focusY: number;
  zoom: number;
};

const CAMERA: Keyframe[] = [
  {frame: 0, focusX: 800, focusY: 500, zoom: 1},
  {frame: 56, focusX: 800, focusY: 500, zoom: 1},
  {frame: 72, focusX: 500, focusY: 500, zoom: 1},
  {frame: 87, focusX: 500, focusY: 500, zoom: 1},
  {frame: 110, focusX: 800, focusY: 500, zoom: 1},
  {frame: 138, focusX: 800, focusY: 500, zoom: 1},
  {frame: 151, focusX: 700, focusY: 515, zoom: 1.12},
  {frame: 175, focusX: 700, focusY: 515, zoom: 1.12},
  {frame: 188, focusX: 800, focusY: 500, zoom: 1},
  {frame: 204, focusX: 500, focusY: 500, zoom: 1},
  {frame: 218, focusX: 500, focusY: 500, zoom: 1},
  {frame: 239, focusX: 900, focusY: 500, zoom: 1},
  {frame: 258, focusX: 900, focusY: 500, zoom: 1},
  {frame: 273, focusX: 930, focusY: 500, zoom: 1.1},
  {frame: 292, focusX: 930, focusY: 500, zoom: 1.1},
  {frame: 306, focusX: 930, focusY: 500, zoom: 1},
  {frame: 318, focusX: 500, focusY: 500, zoom: 1},
  {frame: 332, focusX: 500, focusY: 500, zoom: 1},
  {frame: 356, focusX: 820, focusY: 500, zoom: 1},
  {frame: 389, focusX: 820, focusY: 500, zoom: 1},
  {frame: 405, focusX: 500, focusY: 500, zoom: 1},
  {frame: 449, focusX: 500, focusY: 500, zoom: 1},
];

const POINTER = [
  {frame: 0, x: 1110, y: 520},
  {frame: 40, x: 1110, y: 520},
  {frame: 72, x: 126, y: 276},
  {frame: 78, x: 126, y: 276},
  {frame: 116, x: 770, y: 520},
  {frame: 151, x: 520, y: 520},
  {frame: 162, x: 520, y: 520},
  {frame: 188, x: 780, y: 610},
  {frame: 204, x: 125, y: 427},
  {frame: 212, x: 125, y: 427},
  {frame: 247, x: 1250, y: 355},
  {frame: 273, x: 930, y: 430},
  {frame: 282, x: 930, y: 430},
  {frame: 306, x: 1060, y: 720},
  {frame: 318, x: 125, y: 504},
  {frame: 326, x: 125, y: 504},
  {frame: 364, x: 770, y: 650},
  {frame: 378, x: 770, y: 650},
  {frame: 405, x: 126, y: 916},
  {frame: 449, x: 126, y: 916},
];

const CLICK_FRAMES = [78, 162, 212, 282, 326, 378];

const values = <T extends Record<string, number>>(
  keyframes: T[],
  key: keyof T,
): number[] => keyframes.map((item) => item[key]);

const animate = (
  frame: number,
  times: number[],
  output: number[],
): number =>
  interpolate(frame, times, output, {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

const cameraAt = (frame: number) => ({
  focusX: animate(frame, values(CAMERA, "frame"), values(CAMERA, "focusX")),
  focusY: animate(frame, values(CAMERA, "frame"), values(CAMERA, "focusY")),
  zoom: animate(frame, values(CAMERA, "frame"), values(CAMERA, "zoom")),
});

const pointerAt = (frame: number) => ({
  x: animate(frame, values(POINTER, "frame"), values(POINTER, "x")),
  y: animate(frame, values(POINTER, "frame"), values(POINTER, "y")),
});

const clickAt = (frame: number): number =>
  Math.max(
    0,
    ...CLICK_FRAMES.map((click) =>
      interpolate(frame, [click - 1, click + 2, click + 12], [0, 1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: Easing.out(Easing.cubic),
      }),
    ),
  );

const screenOpacity = (
  frame: number,
  start: number,
  end: number,
): number =>
  interpolate(frame, [start, start + 4, end - 4, end], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const CursorGlyph: React.FC<{
  x: number;
  y: number;
  scale?: number;
}> = ({x, y, scale = 1}) => (
  <svg
    width={42}
    height={52}
    viewBox="0 0 44 54"
    style={{
      position: "absolute",
      left: x,
      top: y,
      transform: `translate(-7px, -5px) scale(${scale})`,
      transformOrigin: "8px 7px",
      filter: "drop-shadow(0 5px 8px rgba(4, 12, 15, .36))",
    }}
  >
    <path
      d="M8 5.5v33.2l8.8-8.3 6.8 15.7 7-3-6.9-15.5h12L8 5.5Z"
      fill={CREAM}
      stroke={INK}
      strokeWidth={2.4}
      strokeLinejoin="round"
    />
  </svg>
);

const OrganicCursor: React.FC = () => {
  const frame = useCurrentFrame();
  const camera = cameraAt(frame);
  const pointer = pointerAt(frame);
  const scale = BASE_SCALE * camera.zoom;
  const x = WIDTH / 2 + (pointer.x - camera.focusX) * scale;
  const y = HEIGHT / 2 + (pointer.y - camera.focusY) * scale;
  const click = clickAt(frame);

  return (
    <>
      {click > 0 ? (
        <div
          style={{
            position: "absolute",
            left: x,
            top: y,
            width: 22 + click * 58,
            height: 22 + click * 58,
            borderRadius: "50%",
            border: `2px solid rgba(210,139,85,${0.9 - click * 0.6})`,
            transform: "translate(-50%, -50%)",
          }}
        />
      ) : null}
      <CursorGlyph x={x} y={y} scale={1 - click * 0.1} />
    </>
  );
};

const ProductCapture: React.FC = () => {
  const frame = useCurrentFrame();
  const camera = cameraAt(frame);
  const previous = cameraAt(Math.max(0, frame - 1));
  const scale = BASE_SCALE * camera.zoom;
  const imageWidth = SOURCE_WIDTH * scale;
  const imageHeight = SOURCE_HEIGHT * scale;
  const imageX = WIDTH / 2 - camera.focusX * scale;
  const imageY = HEIGHT / 2 - camera.focusY * scale;
  const motion =
    Math.abs(camera.zoom - previous.zoom) * 50 +
    Math.hypot(
      camera.focusX - previous.focusX,
      camera.focusY - previous.focusY,
    ) *
      0.008;
  const blur = Math.min(1.25, motion);

  const screens = [
    {
      src: staticFile("statement.png"),
      opacity: interpolate(frame, [0, 78, 82], [1, 1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
    },
    {
      src: staticFile("discoveries.png"),
      opacity: screenOpacity(frame, 78, 216),
    },
    {
      src: staticFile("advisor.png"),
      opacity: screenOpacity(frame, 212, 330),
    },
    {
      src: staticFile("import.png"),
      opacity: interpolate(frame, [326, 330, 449], [0, 1, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
    },
  ];

  return (
    <AbsoluteFill style={{background: "#f2eee6", overflow: "hidden"}}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          filter: `blur(${blur}px)`,
        }}
      >
        {screens.map((screen) => (
          <Img
            key={screen.src}
            src={screen.src}
            style={{
              position: "absolute",
              left: imageX,
              top: imageY,
              width: imageWidth,
              height: imageHeight,
              opacity: screen.opacity,
            }}
          />
        ))}
      </div>
      <OrganicCursor />
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          boxShadow: "inset 0 0 100px rgba(23,39,44,.05)",
        }}
      />
    </AbsoluteFill>
  );
};

export const OrganicFilm: React.FC = () => {
  const frame = useCurrentFrame();
  const fade = interpolate(frame, [442, 449], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{background: INK}}>
      <div style={{position: "absolute", inset: 0, opacity: fade}}>
        <ProductCapture />
      </div>
      <Audio src={staticFile("soundtrack.wav")} />
    </AbsoluteFill>
  );
};
