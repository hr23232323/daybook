import React from "react";
import {Composition} from "remotion";
import {LaunchFilm} from "./LaunchFilm";
import {OrganicFilm} from "./OrganicFilm";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DaybookSquare"
        component={LaunchFilm}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1080}
      />
      <Composition
        id="DaybookOrganic"
        component={OrganicFilm}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1080}
      />
    </>
  );
};
