import {roundValueForPresentation as r} from 'cad/craft/operationHelper';
import {ApplicationContext} from "cad/context";
import {EntityKind} from "cad/model/entities";
import {OperationDescriptor} from "cad/craft/operationBundle";
import {SetLocation} from "cad/craft/e0/interact";
import {MDatum} from "cad/model/mdatum";
import icon from "./HOLE.svg";
import { MFace } from 'cad/model/mface';
import {Matrix3x4} from "math/matrix";
import {BooleanDefinition} from "cad/craft/schema/common/BooleanDefinition";
import { applyRotation } from 'cad/craft/datum/rotate/rotateDatumOperation';
import CSysObject3D from 'cad/craft/datum/csysObject';
import { Circle } from 'cad/sketch/sketchModel';



interface HoleParams {
  datum: MDatum | MFace;
  diameter: number;
  depth: number;
  counterBoreDiameter: number;
  counterBoreDepth: number;
  countersinkDiameter: number;
  countersinkAngle: number;
  holeType: string;
  boolean: BooleanDefinition;
  invertDirection: boolean;
}

export const HoleOperation: OperationDescriptor<HoleParams> = {
  id: 'HOLE_TOOL',
  label: 'hole',
  icon,
  info: 'creates hole features',
  path:__dirname,
  paramsInfo: ({

    diameter,
    depth,
    counterBoreDiameter,
    counterBoreDepth,
    countersinkDiameter,
    countersinkAngle,
    holeType,
  }) => `(${r(depth)} ${r(counterBoreDiameter)})  ${r(counterBoreDepth)})`,

  run: (params: HoleParams, ctx: ApplicationContext) => {
    const occ = ctx.occService;
    const oci = occ.commandInterface;

    const returnObject = {
      consumed: [],
      created: []
    };



    oci.pcylinder("result", params.diameter / 2, params.depth);

    if (params.holeType == "counterbore") {
      oci.pcylinder("counterbore", params.counterBoreDiameter / 2, params.counterBoreDepth);

      oci.bop("result", "counterbore");
      oci.bopfuse("result");
    }

    if (params.holeType == "countersink") {

      const heightFromDiameterAndAngle = (params.countersinkDiameter - params.diameter) / (Math.tan((params.countersinkAngle / 180 * Math.PI) / 2));


      oci.pcone("countersink", params.countersinkDiameter / 2, 0, heightFromDiameterAndAngle);
      oci.bop("result", "countersink");
      oci.bopfuse("result");
    }


    const sketch = ctx.sketchStorageService.readSketch(params.datum.id);
    console.log("this is the sketch data" , sketch);

    const holeSolids = [];


    sketch.loops.forEach((holePoint,i) =>{
      console.log(holePoint);

      if (holePoint instanceof Circle){
        const NewHoleName = "hole" + i;
        oci.copy("result", NewHoleName);

        const flipped = new Matrix3x4();
        if (params.invertDirection === false) flipped.myy = -1;


        const tr = new Matrix3x4().setTranslation(holePoint.c.x, holePoint.c.y, holePoint.c.z);
        const location = params.datum.csys.outTransformation.combine(tr.combine(flipped));
        SetLocation(NewHoleName, location.toFlatArray());
        holeSolids.push(occ.io.getShell(NewHoleName));
      }
    })

    sketch.points.forEach((holePoint,i) =>{
      console.log(holePoint);


        const NewHoleName = "hole" + i;
        oci.copy("result", NewHoleName);

        const flipped = new Matrix3x4();
        if (params.invertDirection === false) flipped.myy = -1;


        const tr = new Matrix3x4().setTranslation(holePoint.point.x, holePoint.point.y, holePoint.point.z);
        const location = params.datum.csys.outTransformation.combine(tr.combine(flipped));
        SetLocation(NewHoleName, location.toFlatArray());
        holeSolids.push(occ.io.getShell(NewHoleName));
      
    })
    

    return occ.utils.applyBooleanModifier(holeSolids, params.boolean);

  
  },
  form: [
    {
      type: 'selection',
      name: 'datum',
      capture: [EntityKind.FACE],
      label: 'Sketch',
      multi: false,
      defaultValue: {
        usePreselection: true,
        preselectionIndex: 0
      },
    },

    {
      type: 'choice',
      label: 'HoleType',
      name: "holeType",
      style: "dropdown",
      defaultValue: "counterbore",
      values: ['counterbore', 'countersink', 'normal',],
    },


    {
      type: 'number',
      name: "diameter",
      defaultValue: 10,
      label: 'Hole ⌀'
    },
    {
      type: 'number',
      name: "depth",
      defaultValue: 100,
      label: 'Hole ↧'
    },


    {
      type: 'number',
      name: "counterBoreDiameter",
      defaultValue: 20,
      label: '⌴ ⌀'
    },
    {
      type: 'number',
      name: "counterBoreDepth",
      defaultValue: 10,
      label: '⌴ ↧'
    },


    {
      type: 'number',
      name: "countersinkDiameter",
      defaultValue: 20,
      label: '⌵ ⌀'
    },
    {
      type: 'number',
      name: "countersinkAngle",
      defaultValue: 90,
      label: '⌵ Angle'
    },

    {
      name: "invertDirection",
      label: 'Invert Direction',
      type: "checkbox",
      defaultValue: false
    },

    {
      type: 'boolean',
      name: 'boolean',
      label: 'boolean',
      optional: true,
      simplify: true,
      defaultValue: "SUBTRACT",
    }
  ],
}
