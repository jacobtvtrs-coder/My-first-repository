import { Composition, Folder } from "remotion";
import { HelloWorld } from "./HelloWorld";
import { Logo } from "./HelloWorld/Logo";
import { Title } from "./HelloWorld/Title";
import { Cuts, cutsDuration, defaultShots } from "./Cuts";
import { BarberCuts, barberCutsDuration } from "./BarberCuts";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="Elements">
        <Composition
          id="Logo"
          component={Logo}
          durationInFrames={150}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            logoColor1: "#91EAE4",
            logoColor2: "#86A8E7",
          }}
        />
        <Composition
          id="Title"
          component={Title}
          durationInFrames={115}
          fps={30}
          width={1920}
          height={1080}
          defaultProps={{
            titleText: "Welcome to Remotion",
            titleColor: "#000000",
          }}
        />
      </Folder>
      <Composition
        // You can take the "id" to render a video:
        // bunx remotion render HelloWorld
        id="HelloWorld"
        component={HelloWorld}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
        // You can override these props for each render:
        // https://www.remotion.dev/docs/parametrized-rendering
        defaultProps={{
          titleText: "Welcome to Remotion",
          titleColor: "#000000",
        }}
      />
      <Composition
        // Vertical 9:16 video made only of hard cuts.
        // Render it with: npx remotion render Cuts
        id="Cuts"
        component={Cuts}
        durationInFrames={cutsDuration(defaultShots)}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ shots: defaultShots }}
      />
      <Composition
        // Before/after hard-cut barber edit. Needs the footage downloaded first:
        // scripts/fetch-footage.sh, then: npx remotion render BarberCuts
        id="BarberCuts"
        component={BarberCuts}
        durationInFrames={barberCutsDuration}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          footage: "footage/Charle_riche.1q4r4Pf-UNEcShn3CIk6PDzx_ylwzokU4.mov",
          beforeStartSec: 4,
          afterStartSec: 58,
          song: "footage/reference-audio.m4a",
          songVolume: 0.6,
          originalVolume: 1,
          originalVolumeOnHold: 1,
        }}
      />
    </>
  );
};
