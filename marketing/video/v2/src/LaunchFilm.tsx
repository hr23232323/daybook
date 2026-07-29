import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const INK = "#17272c";
const DEEP = "#0b171b";
const CREAM = "#f7f3eb";
const PAPER = "#efe9de";
const ORANGE = "#d28b55";
const SAGE = "#b9d8cc";
const MIST = "#7f9298";

const APP_X = 52;
const APP_Y = 226;
const APP_W = 976;
const APP_H = 654;
const CHROME_H = 44;
const VIEW_W = APP_W;
const VIEW_H = 610;
const SOURCE_W = 1600;
const SOURCE_H = 1000;

const CAMERA_TIMES = [
  0, 24, 46, 74, 94, 108, 116, 146, 178, 200, 208, 246, 286, 308, 316,
  348, 380, 398,
];
const CAMERA_ZOOM = [
  1.28, 1.0, 1.1, 1.34, 1.08, 1.22, 1.08, 1.38, 1.08, 1.2, 1.08, 1.42,
  1.1, 1.2, 1.08, 1.4, 1.08, 1.0,
];
const CAMERA_FOCUS_X = [
  920, 800, 930, 900, 800, 150, 150, 880, 800, 150, 150, 900, 800, 150,
  150, 620, 800, 800,
];
const CAMERA_FOCUS_Y = [
  280, 500, 360, 380, 500, 210, 210, 585, 500, 295, 295, 430, 500, 338,
  338, 470, 500, 500,
];

const POINTER_TIMES = [
  0, 16, 44, 68, 86, 108, 116, 145, 174, 200, 208, 232, 270, 295, 308,
  316, 350, 380, 398,
];
const POINTER_X = [
  900, 1000, 1170, 900, 800, 125, 125, 600, 1000, 125, 125, 1200, 780,
  1000, 125, 125, 600, 1000, 800,
];
const POINTER_Y = [
  280, 310, 650, 380, 500, 208, 208, 540, 650, 295, 295, 200, 400, 600,
  338, 338, 590, 500, 500,
];

const CLICK_FRAMES = [68, 108, 145, 200, 232, 270, 308, 350];

const smooth = (
  frame: number,
  input: number[],
  output: number[],
): number => {
  return interpolate(frame, input, output, {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
};

const sceneOpacity = (
  frame: number,
  start: number,
  end: number,
  fade = 10,
): number => {
  return interpolate(
    frame,
    [start, start + fade, end - fade, end],
    [0, 1, 1, 0],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
  );
};

const cameraAt = (frame: number) => ({
  zoom: smooth(frame, CAMERA_TIMES, CAMERA_ZOOM),
  focusX: smooth(frame, CAMERA_TIMES, CAMERA_FOCUS_X),
  focusY: smooth(frame, CAMERA_TIMES, CAMERA_FOCUS_Y),
});

const pointerSourceAt = (frame: number) => ({
  x: smooth(frame, POINTER_TIMES, POINTER_X),
  y: smooth(frame, POINTER_TIMES, POINTER_Y),
});

const pointerInViewportAt = (frame: number) => {
  const camera = cameraAt(frame);
  const pointer = pointerSourceAt(frame);
  const imageW = VIEW_W * camera.zoom;
  const imageH = VIEW_H * camera.zoom;
  const imageX =
    VIEW_W / 2 - (camera.focusX / SOURCE_W) * imageW;
  const imageY =
    VIEW_H / 2 - (camera.focusY / SOURCE_H) * imageH;
  return {
    x: imageX + (pointer.x / SOURCE_W) * imageW,
    y: imageY + (pointer.y / SOURCE_H) * imageH,
  };
};

const clickStrengthAt = (frame: number): number => {
  return Math.max(
    0,
    ...CLICK_FRAMES.map((click) =>
      interpolate(frame, [click - 1, click + 2, click + 13], [0, 1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: Easing.out(Easing.cubic),
      }),
    ),
  );
};

const CursorGlyph: React.FC<{
  x: number;
  y: number;
  opacity?: number;
  scale?: number;
  rotation?: number;
  ghost?: boolean;
}> = ({x, y, opacity = 1, scale = 1, rotation = 0, ghost = false}) => {
  return (
    <svg
      width={44}
      height={54}
      viewBox="0 0 44 54"
      style={{
        position: "absolute",
        left: x,
        top: y,
        opacity,
        transform: `translate(-7px, -5px) rotate(${rotation}deg) scale(${scale})`,
        transformOrigin: "8px 7px",
        filter: ghost
          ? "blur(1.2px)"
          : "drop-shadow(0 5px 8px rgba(4, 12, 15, .34))",
      }}
    >
      <path
        d="M8 5.5v33.2l8.8-8.3 6.8 15.7 7-3-6.9-15.5h12L8 5.5Z"
        fill={ghost ? ORANGE : CREAM}
        stroke={ghost ? ORANGE : INK}
        strokeWidth={ghost ? 1.5 : 2.4}
        strokeLinejoin="round"
      />
    </svg>
  );
};

const Cursor: React.FC = () => {
  const frame = useCurrentFrame();
  const point = pointerInViewportAt(frame);
  const previous = pointerInViewportAt(Math.max(0, frame - 1));
  const velocityX = point.x - previous.x;
  const rotation = Math.max(-7, Math.min(7, velocityX * 0.18));
  const click = clickStrengthAt(frame);
  const opacity = interpolate(frame, [4, 12, 382, 394], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <>
      {[4.5, 3, 1.5].map((lag, index) => {
        const ghostPoint = pointerInViewportAt(Math.max(0, frame - lag));
        return (
          <CursorGlyph
            key={lag}
            x={ghostPoint.x}
            y={ghostPoint.y}
            opacity={opacity * (0.035 + index * 0.025)}
            rotation={rotation}
            ghost
          />
        );
      })}
      {click > 0 ? (
        <>
          <div
            style={{
              position: "absolute",
              left: point.x,
              top: point.y,
              width: 74 + click * 34,
              height: 74 + click * 34,
              borderRadius: "50%",
              border: `3px solid ${ORANGE}`,
              transform: "translate(-50%, -50%)",
              opacity: (1 - click) * 0.75,
              boxShadow: `0 0 28px rgba(210, 139, 85, ${0.28 * (1 - click)})`,
            }}
          />
          <div
            style={{
              position: "absolute",
              left: point.x,
              top: point.y,
              width: 18 + click * 16,
              height: 18 + click * 16,
              borderRadius: "50%",
              background: ORANGE,
              transform: "translate(-50%, -50%)",
              opacity: (1 - click) * 0.55,
            }}
          />
        </>
      ) : null}
      <CursorGlyph
        x={point.x}
        y={point.y}
        opacity={opacity}
        rotation={rotation}
        scale={1 - click * 0.12}
      />
    </>
  );
};

const screenOpacity = (
  frame: number,
  start: number,
  end: number,
): number => {
  return interpolate(frame, [start, start + 7, end - 7, end], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

const ProductWindow: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const camera = cameraAt(frame);
  const previousCamera = cameraAt(Math.max(0, frame - 1));
  const pointer = pointerSourceAt(frame);
  const imageW = VIEW_W * camera.zoom;
  const imageH = VIEW_H * camera.zoom;
  const imageX = VIEW_W / 2 - (camera.focusX / SOURCE_W) * imageW;
  const imageY = VIEW_H / 2 - (camera.focusY / SOURCE_H) * imageH;

  const reveal = spring({
    frame,
    fps,
    durationInFrames: 30,
    config: {damping: 22, stiffness: 115, mass: 0.8},
  });
  const exit = spring({
    frame: frame - 392,
    fps,
    durationInFrames: 28,
    config: {damping: 24, stiffness: 120},
  });
  const cardScale = interpolate(reveal, [0, 1], [1.2, 1]) * (1 - exit * 0.2);
  const cardY = interpolate(reveal, [0, 1], [42, 0]) + exit * 80;
  const cardOpacity = interpolate(exit, [0, 1], [1, 0]);
  const radius = interpolate(reveal, [0, 1], [4, 28]);
  const tiltY = ((pointer.x - 800) / 800) * 1.35 * (1 - exit);
  const tiltX = -((pointer.y - 500) / 500) * 0.82 * (1 - exit);
  const cameraVelocity =
    Math.abs(camera.zoom - previousCamera.zoom) * 48 +
    Math.hypot(
      camera.focusX - previousCamera.focusX,
      camera.focusY - previousCamera.focusY,
    ) *
      0.005;
  const blur = Math.min(1.8, cameraVelocity);

  const swapFlash = Math.max(
    0,
    ...[108, 200, 308].map((cut) =>
      interpolate(frame, [cut, cut + 4, cut + 10], [0, 0.24, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
    ),
  );

  const screens = [
    {
      src: staticFile("statement.png"),
      opacity: interpolate(frame, [0, 108, 115], [1, 1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
    },
    {
      src: staticFile("discoveries.png"),
      opacity: screenOpacity(frame, 108, 207),
    },
    {
      src: staticFile("advisor.png"),
      opacity: screenOpacity(frame, 200, 315),
    },
    {
      src: staticFile("import.png"),
      opacity: interpolate(frame, [308, 315, 392], [0, 1, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }),
    },
  ];

  const lightSweep = interpolate(frame, [0, 44], [-280, 1260], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  return (
    <div
      style={{
        position: "absolute",
        left: APP_X,
        top: APP_Y,
        width: APP_W,
        height: APP_H,
        opacity: cardOpacity,
        transform: `translateY(${cardY}px) perspective(1800px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale(${cardScale})`,
        transformOrigin: "50% 45%",
        borderRadius: radius,
        background: CREAM,
        boxShadow:
          "0 50px 110px rgba(0, 0, 0, .46), 0 18px 44px rgba(3, 11, 14, .34), inset 0 0 0 1px rgba(255,255,255,.32)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          height: CHROME_H,
          background:
            "linear-gradient(180deg, rgba(250,248,243,.98), rgba(231,226,216,.98))",
          borderBottom: "1px solid rgba(23,39,44,.14)",
          display: "flex",
          alignItems: "center",
          position: "relative",
          zIndex: 8,
        }}
      >
        <div style={{display: "flex", gap: 8, marginLeft: 18}}>
          {[ORANGE, "#d9b56f", "#6f9f8c"].map((color) => (
            <div
              key={color}
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: color,
                boxShadow: "inset 0 0 0 1px rgba(23,39,44,.12)",
              }}
            />
          ))}
        </div>
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: 8,
            transform: "translateX(-50%)",
            height: 28,
            minWidth: 270,
            padding: "0 24px",
            borderRadius: 14,
            background: "rgba(23,39,44,.07)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 9,
            fontFamily: "Arial, sans-serif",
            fontSize: 12,
            letterSpacing: 1.1,
            color: "#53636a",
          }}
        >
          <span style={{fontSize: 10}}>●</span>
          daybook.local
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 0,
          top: CHROME_H,
          width: VIEW_W,
          height: VIEW_H,
          overflow: "hidden",
          background: PAPER,
        }}
      >
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
                width: imageW,
                height: imageH,
                opacity: screen.opacity,
              }}
            />
          ))}
        </div>
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `rgba(247,243,235,${swapFlash})`,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: lightSweep,
            top: -180,
            width: 170,
            height: 980,
            transform: "rotate(18deg)",
            background:
              "linear-gradient(90deg, transparent, rgba(255,255,255,.18), transparent)",
            opacity: 0.8,
          }}
        />
        <Cursor />
      </div>
    </div>
  );
};

type HeadlineScene = {
  start: number;
  end: number;
  index: string;
  first: string;
  emphasis: string;
  rail: string;
};

const HEADLINES: HeadlineScene[] = [
  {
    start: 0,
    end: 111,
    index: "01 / 04",
    first: "Your money.",
    emphasis: "Finally legible.",
    rail: "NET POSITION  ·  CASH FLOW  ·  SPENDING RHYTHM",
  },
  {
    start: 108,
    end: 203,
    index: "02 / 04",
    first: "Patterns",
    emphasis: "worth noticing.",
    rail: "COMPUTED LOCALLY  ·  OPEN ANY NUMBER",
  },
  {
    start: 200,
    end: 311,
    index: "03 / 04",
    first: "Ask",
    emphasis: "your ledger.",
    rail: "READ-ONLY TOOLS  ·  ADJUSTABLE THINKING  ·  GROUNDED",
  },
  {
    start: 308,
    end: 398,
    index: "04 / 04",
    first: "Bring your records",
    emphasis: "home.",
    rail: "CSV  ·  OFX  ·  QFX  ·  SIMPLEFIN",
  },
];

const Header: React.FC = () => {
  const frame = useCurrentFrame();
  const exit = interpolate(frame, [386, 402], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div style={{opacity: exit}}>
      <div
        style={{
          position: "absolute",
          left: 54,
          top: 34,
          display: "flex",
          alignItems: "center",
          gap: 13,
        }}
      >
        <Img
          src={staticFile("daybook-mark.svg")}
          style={{width: 38, height: 38, borderRadius: 10}}
        />
        <div
          style={{
            color: CREAM,
            fontFamily: "Arial, sans-serif",
            fontSize: 17,
            fontWeight: 700,
            letterSpacing: 0.3,
          }}
        >
          Daybook
        </div>
        <div
          style={{
            width: 1,
            height: 19,
            background: "rgba(247,243,235,.25)",
            marginLeft: 4,
          }}
        />
        <div
          style={{
            color: SAGE,
            fontFamily: "Arial, sans-serif",
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: 2.1,
          }}
        >
          PRIVATE MONEY
        </div>
      </div>

      {HEADLINES.map((scene) => {
        const opacity =
          scene.start === 0
            ? interpolate(frame, [4, 16, scene.end - 10, scene.end], [0, 1, 1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })
            : sceneOpacity(frame, scene.start, scene.end);
        const enter = interpolate(
          frame,
          [scene.start, scene.start + 15],
          [22, 0],
          {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
        );
        return (
          <React.Fragment key={scene.index}>
            <div
              style={{
                position: "absolute",
                left: 54,
                top: 93 + enter,
                display: "flex",
                alignItems: "baseline",
                gap: 18,
                opacity,
                whiteSpace: "nowrap",
              }}
            >
              <span
                style={{
                  color: CREAM,
                  fontFamily: "Arial, sans-serif",
                  fontSize: 49,
                  fontWeight: 760,
                  letterSpacing: -1.9,
                }}
              >
                {scene.first}
              </span>
              <span
                style={{
                  color: ORANGE,
                  fontFamily: "Georgia, serif",
                  fontSize: 51,
                  fontWeight: 700,
                  letterSpacing: -1.6,
                  fontStyle: "italic",
                }}
              >
                {scene.emphasis}
              </span>
            </div>
            <div
              style={{
                position: "absolute",
                right: 55,
                top: 48,
                color: MIST,
                fontFamily: "Arial, sans-serif",
                fontSize: 12,
                fontWeight: 700,
                letterSpacing: 2.5,
                opacity,
              }}
            >
              {scene.index}
            </div>
            <div
              style={{
                position: "absolute",
                left: 54,
                top: 927,
                color: SAGE,
                fontFamily: "Arial, sans-serif",
                fontSize: 14,
                fontWeight: 700,
                letterSpacing: 2.4,
                opacity,
              }}
            >
              {scene.rail}
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

const Backdrop: React.FC = () => {
  const frame = useCurrentFrame();
  const point = pointerInViewportAt(Math.min(390, frame));
  const glowX = APP_X + point.x;
  const glowY = APP_Y + CHROME_H + point.y;
  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 18% 18%, #19383c 0, #101f24 31%, #091418 74%)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: glowX - 340,
          top: glowY - 340,
          width: 680,
          height: 680,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(185,216,204,.15), rgba(185,216,204,0) 67%)",
          transform: `scale(${1 + Math.sin(frame / 34) * 0.05})`,
        }}
      />
      <div
        style={{
          position: "absolute",
          right: -280 + Math.sin(frame / 55) * 35,
          top: -240 + Math.cos(frame / 60) * 28,
          width: 650,
          height: 650,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(210,139,85,.17), rgba(210,139,85,0) 68%)",
          filter: "blur(5px)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.12,
          backgroundImage:
            "radial-gradient(rgba(247,243,235,.5) 0.8px, transparent 0.8px)",
          backgroundSize: "34px 34px",
          transform: `translate(${(frame * 0.07) % 34}px, ${(frame * 0.04) % 34}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(2,8,10,.02), rgba(2,8,10,.22))",
        }}
      />
    </AbsoluteFill>
  );
};

const EndCursor: React.FC = () => {
  const frame = useCurrentFrame();
  const x = smooth(frame, [404, 430], [858, 742]);
  const y = smooth(frame, [404, 430], [584, 708]);
  const opacity = interpolate(frame, [404, 411, 442, 449], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const click = interpolate(frame, [430, 433, 444], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <>
      {[5, 3, 1].map((lag, index) => {
        const trailX = smooth(frame - lag, [404, 430], [858, 742]);
        const trailY = smooth(frame - lag, [404, 430], [584, 708]);
        return (
          <CursorGlyph
            key={lag}
            x={trailX}
            y={trailY}
            opacity={opacity * (0.03 + index * 0.025)}
            ghost
          />
        );
      })}
      {click > 0 ? (
        <div
          style={{
            position: "absolute",
            left: x,
            top: y,
            width: 52 + click * 64,
            height: 52 + click * 64,
            borderRadius: "50%",
            border: `3px solid ${ORANGE}`,
            transform: "translate(-50%, -50%)",
            opacity: (1 - click) * 0.8,
          }}
        />
      ) : null}
      <CursorGlyph
        x={x}
        y={y}
        opacity={opacity}
        scale={1 - click * 0.12}
      />
    </>
  );
};

const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = interpolate(frame, [392, 408], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const logo = spring({
    frame: frame - 396,
    fps,
    durationInFrames: 32,
    config: {damping: 17, stiffness: 130, mass: 0.72},
  });
  const copy = spring({
    frame: frame - 403,
    fps,
    durationInFrames: 34,
    config: {damping: 22, stiffness: 112},
  });
  const pill = spring({
    frame: frame - 412,
    fps,
    durationInFrames: 30,
    config: {damping: 20, stiffness: 130},
  });
  const clicked = interpolate(frame, [430, 433, 443], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{opacity}}>
      <div
        style={{
          position: "absolute",
          left: 174,
          top: 145,
          width: 732,
          height: 732,
          borderRadius: "50%",
          border: "1px solid rgba(185,216,204,.12)",
          transform: `scale(${0.88 + logo * 0.12})`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 269,
          top: 240,
          width: 542,
          height: 542,
          borderRadius: "50%",
          background:
            "radial-gradient(circle, rgba(185,216,204,.08), rgba(185,216,204,0) 70%)",
        }}
      />
      <Img
        src={staticFile("daybook-mark.svg")}
        style={{
          position: "absolute",
          left: 484,
          top: 210 - (1 - logo) * 52,
          width: 112,
          height: 112,
          borderRadius: 25,
          opacity: logo,
          transform: `scale(${0.7 + logo * 0.3})`,
          boxShadow: "0 26px 70px rgba(0,0,0,.32)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 362,
          width: "100%",
          textAlign: "center",
          color: CREAM,
          fontFamily: "Georgia, serif",
          fontSize: 92,
          fontWeight: 700,
          letterSpacing: -3.2,
          opacity: copy,
          transform: `translateY(${(1 - copy) * 36}px)`,
        }}
      >
        Daybook
      </div>
      <div
        style={{
          position: "absolute",
          top: 481,
          width: "100%",
          textAlign: "center",
          color: SAGE,
          fontFamily: "Arial, sans-serif",
          fontSize: 24,
          fontWeight: 500,
          letterSpacing: 0.3,
          opacity: copy,
        }}
      >
        A private record of your money.
      </div>
      <div
        style={{
          position: "absolute",
          left: 193,
          top: 649 + (1 - pill) * 36,
          width: 694,
          height: 104,
          borderRadius: 52,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: clicked > 0.35 ? INK : CREAM,
          background:
            clicked > 0.35 ? CREAM : "rgba(247,243,235,.08)",
          border: `2px solid ${clicked > 0.35 ? CREAM : "rgba(247,243,235,.42)"}`,
          boxShadow:
            clicked > 0.35
              ? "0 0 52px rgba(210,139,85,.3)"
              : "0 24px 70px rgba(0,0,0,.22)",
          fontFamily: "Arial, sans-serif",
          fontSize: 24,
          fontWeight: 700,
          letterSpacing: 0.2,
          opacity: pill,
          transform: `scale(${0.92 + pill * 0.08})`,
        }}
      >
        github.com/hr23232323/daybook
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 82,
          width: "100%",
          textAlign: "center",
          color: ORANGE,
          fontFamily: "Arial, sans-serif",
          fontSize: 14,
          fontWeight: 800,
          letterSpacing: 4.3,
          opacity: pill,
        }}
      >
        LOCAL-FIRST · OPEN SOURCE · MIT
      </div>
      <EndCursor />
    </AbsoluteFill>
  );
};

export const LaunchFilm: React.FC = () => {
  return (
    <AbsoluteFill>
      <Backdrop />
      <ProductWindow />
      <Header />
      <Outro />
      <Audio src={staticFile("soundtrack.wav")} volume={0.92} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          boxShadow: "inset 0 0 0 1px rgba(255,255,255,.035)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
