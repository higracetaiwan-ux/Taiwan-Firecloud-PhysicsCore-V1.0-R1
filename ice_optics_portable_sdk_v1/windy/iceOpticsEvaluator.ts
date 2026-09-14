// Firecloud Ice Optics portable TypeScript evaluator for WINDY/Svelte.
// Standalone consumer implementation: no PhysicsCore/Python/Streamlit runtime dependency.
export const WAVELENGTHS_NM = [550,575,600,650,700,750] as const;
export const EVALUATOR_VERSION = "ICE_OPTICS_EVALUATOR_V1";
export type IceOpticsInput = { iwp_kg_m2:number|null; native_vertical_completeness:number|null; effective_radius_um:number|null; ice_habit:string|null; surface_roughness:string|null };
export type IceLutRow = { wavelength_nm:number; effective_radius_um:number; ice_habit:string; surface_roughness:string; mass_extinction_coefficient_m2_kg:number; single_scattering_albedo:number; asymmetry_parameter:number; [key:string]:unknown };
export type IceBandResult = { k_ext_m2_kg:number|null; tau:number; transmission:number; ssa:number|null; g:number|null };
export type IceOpticsResult = { evaluator_version:string; contract_version:string; state:string; missing_reason:string; iwp_kg_m2:number|null; native_vertical_completeness:number|null; effective_radius_um:number|null; ice_habit:string; surface_roughness:string; lookup_state?:string; bands:Record<string,IceBandResult> };
const finite=(x:unknown):boolean => x !== null && x !== undefined && x !== '' && Number.isFinite(Number(x));
const approx=(a:unknown,b:unknown,tol=1e-9):boolean => Math.abs(Number(a)-Number(b)) <= tol;
function groupRows(lut:IceLutRow[], habit:string, roughness:string):IceLutRow[]{return lut.filter(r=>String(r.ice_habit)===String(habit)&&String(r.surface_roughness)===String(roughness));}
function lookup(lut:IceLutRow[],habit:string,roughness:string,reff:number):{state:string;rows:IceLutRow[]}{
  const sub=groupRows(lut,habit,roughness); if(!sub.length)return{state:"ICE_HABIT_ROUGHNESS_NOT_IN_LUT",rows:[]};
  const radii=[...new Set(sub.map(r=>Number(r.effective_radius_um)))].filter(Number.isFinite).sort((a,b)=>a-b);
  if(!finite(reff))return{state:"ICE_EFFECTIVE_RADIUS_MISSING",rows:[]};
  const r=Number(reff); if(!radii.length||r<radii[0]-1e-12||r>radii[radii.length-1]+1e-12)return{state:"ICE_REFF_OUTSIDE_LUT_DOMAIN",rows:[]};
  const exact=radii.find(x=>approx(x,r)); if(exact!==undefined)return{state:"EXACT_REFF_LUT_ROW",rows:sub.filter(x=>approx(x.effective_radius_um,exact))};
  const hi=radii.findIndex(x=>x>r),lo=hi-1; if(lo<0||hi<0)return{state:"ICE_REFF_OUTSIDE_LUT_DOMAIN",rows:[]};
  const r0=radii[lo],r1=radii[hi],w=(r-r0)/(r1-r0),out:IceLutRow[]=[];
  for(const wl of WAVELENGTHS_NM){
    const a=sub.find(x=>Number(x.wavelength_nm)===wl&&approx(x.effective_radius_um,r0)); const b=sub.find(x=>Number(x.wavelength_nm)===wl&&approx(x.effective_radius_um,r1));
    if(!a||!b)return{state:"ICE_LUT_SIX_BAND_GROUP_INCOMPLETE",rows:[]}; const lerp=(x:unknown,y:unknown)=>Number(x)+w*(Number(y)-Number(x));
    out.push({wavelength_nm:wl,effective_radius_um:r,ice_habit:String(habit),surface_roughness:String(roughness),mass_extinction_coefficient_m2_kg:lerp(a.mass_extinction_coefficient_m2_kg,b.mass_extinction_coefficient_m2_kg),single_scattering_albedo:lerp(a.single_scattering_albedo,b.single_scattering_albedo),asymmetry_parameter:lerp(a.asymmetry_parameter,b.asymmetry_parameter)});
  }
  return{state:"LINEAR_REFF_INTERPOLATION_WITHIN_LUT",rows:out};
}
export function evaluateIceOptics(input:IceOpticsInput,lut:IceLutRow[]):IceOpticsResult{
  const iwp=input?.iwp_kg_m2,vc=input?.native_vertical_completeness,reff=input?.effective_radius_um,habit=input?.ice_habit??"UNKNOWN",rough=input?.surface_roughness??"UNKNOWN";
  const out:IceOpticsResult={evaluator_version:EVALUATOR_VERSION,contract_version:"FIRECLOUD_ICE_OPTICS_V1",state:"UNKNOWN",missing_reason:"",iwp_kg_m2:finite(iwp)?Number(iwp):null,native_vertical_completeness:finite(vc)?Number(vc):null,effective_radius_um:finite(reff)?Number(reff):null,ice_habit:String(habit||"UNKNOWN"),surface_roughness:String(rough||"UNKNOWN"),bands:{}};
  if(!finite(iwp)){out.state="ICE_IWP_MISSING";out.missing_reason="NATIVE_IWP_MISSING";return out;}
  if(!finite(vc)||Number(vc)<1-1e-12){out.state="ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT";out.missing_reason="NATIVE_VERTICAL_COMPLETENESS_LT_1";return out;}
  if(Number(iwp)<0){out.state="ICE_IWP_INVALID";out.missing_reason="NEGATIVE_IWP";return out;}
  if(Math.abs(Number(iwp))<=1e-15){out.state="NO_ICE_CONDENSATE_AT_NATIVE_STATE";for(const wl of WAVELENGTHS_NM)out.bands[String(wl)]={k_ext_m2_kg:null,tau:0,transmission:1,ssa:null,g:null};return out;}
  if(!finite(reff)){out.state="ICE_EFFECTIVE_RADIUS_MISSING";out.missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_REFF";return out;}
  if(!habit||String(habit).toUpperCase()==="UNKNOWN"){out.state="ICE_HABIT_MISSING";out.missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_HABIT";return out;}
  if(!rough||String(rough).toUpperCase()==="UNKNOWN"){out.state="ICE_ROUGHNESS_MISSING";out.missing_reason="NO_CALIBRATED_ICE_ROUGHNESS";return out;}
  const found=lookup(lut,String(habit),String(rough),Number(reff)); if(!found.rows.length){out.state=found.state;out.missing_reason=found.state;return out;}
  out.state="ICE_SIX_BAND_OPTICS_READY";out.lookup_state=found.state;
  for(const r of found.rows){const wl=Number(r.wavelength_nm),k=Number(r.mass_extinction_coefficient_m2_kg),tau=Number(iwp)*k;out.bands[String(wl)]={k_ext_m2_kg:k,tau,transmission:Math.exp(-tau),ssa:Number(r.single_scattering_albedo),g:Number(r.asymmetry_parameter)};}
  return out;
}
