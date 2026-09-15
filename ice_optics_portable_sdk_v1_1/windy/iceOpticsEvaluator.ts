// Firecloud Ice Optics portable Dmax-first TypeScript evaluator for WINDY/Svelte.
export const WAVELENGTHS_NM = [550,575,600,650,700,750] as const;
export const EVALUATOR_VERSION = "ICE_OPTICS_EVALUATOR_V1_1";
export const PORTABLE_CONTRACT_VERSION = "FIRECLOUD_ICE_OPTICS_PORTABLE_V1_1";
export type IceOpticsInput = { iwp_kg_m2:number|null; native_vertical_completeness:number|null; maximum_dimension_um:number|null; ice_habit:string|null; surface_roughness:string|null };
export type IceLutRow = { wavelength_nm:number; maximum_dimension_um:number; effective_diameter_um:number; effective_radius_um:number; ice_habit:string; surface_roughness:string; mass_extinction_coefficient_m2_kg:number; single_scattering_albedo:number; asymmetry_parameter:number; [key:string]:unknown };
export type IceBandResult = { k_ext_m2_kg:number|null; tau:number; transmission:number; ssa:number|null; g:number|null; source_effective_radius_um:number|null };
export type IceOpticsResult = { evaluator_version:string; contract_version:string; portable_contract_version:string; state:string; missing_reason:string; iwp_kg_m2:number|null; native_vertical_completeness:number|null; maximum_dimension_um:number|null; ice_habit:string; surface_roughness:string; lookup_state?:string; bands:Record<string,IceBandResult> };
const finite=(x:unknown):boolean => x !== null && x !== undefined && x !== '' && Number.isFinite(Number(x));
const approx=(a:unknown,b:unknown,tol=1e-9):boolean => Math.abs(Number(a)-Number(b)) <= tol;
function groupRows(lut:IceLutRow[], habit:string, roughness:string):IceLutRow[]{return lut.filter(r=>String(r.ice_habit)===String(habit)&&String(r.surface_roughness)===String(roughness));}
function lookup(lut:IceLutRow[],habit:string,roughness:string,dmax:number):{state:string;rows:IceLutRow[]}{
  const sub=groupRows(lut,habit,roughness); if(!sub.length)return{state:"ICE_HABIT_ROUGHNESS_NOT_IN_LUT",rows:[]};
  const dims=[...new Set(sub.map(r=>Number(r.maximum_dimension_um)))].filter(Number.isFinite).sort((a,b)=>a-b);
  if(!finite(dmax))return{state:"ICE_MAXIMUM_DIMENSION_MISSING",rows:[]};
  const d=Number(dmax); if(!dims.length||d<dims[0]-1e-12||d>dims[dims.length-1]+1e-12)return{state:"ICE_DMAX_OUTSIDE_LUT_DOMAIN",rows:[]};
  const exact=dims.find(x=>approx(x,d)); if(exact!==undefined){const rows=sub.filter(x=>approx(x.maximum_dimension_um,exact));if(new Set(rows.map(x=>Number(x.wavelength_nm))).size!==WAVELENGTHS_NM.length)return{state:"ICE_LUT_SIX_BAND_GROUP_INCOMPLETE",rows:[]};return{state:"EXACT_DMAX_LUT_ROW",rows};}
  const hi=dims.findIndex(x=>x>d),lo=hi-1; if(lo<0||hi<0)return{state:"ICE_DMAX_OUTSIDE_LUT_DOMAIN",rows:[]};
  const d0=dims[lo],d1=dims[hi],w=(d-d0)/(d1-d0),out:IceLutRow[]=[];
  for(const wl of WAVELENGTHS_NM){
    const a=sub.find(x=>Number(x.wavelength_nm)===wl&&approx(x.maximum_dimension_um,d0)); const b=sub.find(x=>Number(x.wavelength_nm)===wl&&approx(x.maximum_dimension_um,d1));
    if(!a||!b)return{state:"ICE_LUT_SIX_BAND_GROUP_INCOMPLETE",rows:[]}; const lerp=(x:unknown,y:unknown)=>Number(x)+w*(Number(y)-Number(x));
    out.push({wavelength_nm:wl,maximum_dimension_um:d,effective_diameter_um:lerp(a.effective_diameter_um,b.effective_diameter_um),effective_radius_um:lerp(a.effective_radius_um,b.effective_radius_um),ice_habit:String(habit),surface_roughness:String(roughness),mass_extinction_coefficient_m2_kg:lerp(a.mass_extinction_coefficient_m2_kg,b.mass_extinction_coefficient_m2_kg),single_scattering_albedo:lerp(a.single_scattering_albedo,b.single_scattering_albedo),asymmetry_parameter:lerp(a.asymmetry_parameter,b.asymmetry_parameter)});
  }
  return{state:"LINEAR_DMAX_INTERPOLATION_WITHIN_LUT",rows:out};
}
export function evaluateIceOptics(input:IceOpticsInput,lut:IceLutRow[]):IceOpticsResult{
  const iwp=input?.iwp_kg_m2,vc=input?.native_vertical_completeness,dmax=input?.maximum_dimension_um,habit=input?.ice_habit??"UNKNOWN",rough=input?.surface_roughness??"UNKNOWN";
  const out:IceOpticsResult={evaluator_version:EVALUATOR_VERSION,contract_version:"FIRECLOUD_ICE_OPTICS_V1",portable_contract_version:PORTABLE_CONTRACT_VERSION,state:"UNKNOWN",missing_reason:"",iwp_kg_m2:finite(iwp)?Number(iwp):null,native_vertical_completeness:finite(vc)?Number(vc):null,maximum_dimension_um:finite(dmax)?Number(dmax):null,ice_habit:String(habit||"UNKNOWN"),surface_roughness:String(rough||"UNKNOWN"),bands:{}};
  if(!finite(iwp)){out.state="ICE_IWP_MISSING";out.missing_reason="NATIVE_IWP_MISSING";return out;}
  if(!finite(vc)||Number(vc)<1-1e-12){out.state="ICE_IWP_INCOMPLETE_NATIVE_VERTICAL_SUPPORT";out.missing_reason="NATIVE_VERTICAL_COMPLETENESS_LT_1";return out;}
  if(Number(iwp)<0){out.state="ICE_IWP_INVALID";out.missing_reason="NEGATIVE_IWP";return out;}
  if(Math.abs(Number(iwp))<=1e-15){out.state="NO_ICE_CONDENSATE_AT_NATIVE_STATE";for(const wl of WAVELENGTHS_NM)out.bands[String(wl)]={k_ext_m2_kg:null,tau:0,transmission:1,ssa:null,g:null,source_effective_radius_um:null};return out;}
  if(!finite(dmax)){out.state="ICE_MAXIMUM_DIMENSION_MISSING";out.missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_DMAX";return out;}
  if(!habit||String(habit).toUpperCase()==="UNKNOWN"){out.state="ICE_HABIT_MISSING";out.missing_reason="NO_NATIVE_OR_CALIBRATED_ICE_HABIT";return out;}
  if(!rough||String(rough).toUpperCase()==="UNKNOWN"){out.state="ICE_ROUGHNESS_MISSING";out.missing_reason="NO_CALIBRATED_ICE_ROUGHNESS";return out;}
  const found=lookup(lut,String(habit),String(rough),Number(dmax)); if(!found.rows.length){out.state=found.state;out.missing_reason=found.state;return out;}
  out.state="ICE_SIX_BAND_OPTICS_READY";out.lookup_state=found.state;
  for(const r of found.rows){const wl=Number(r.wavelength_nm),k=Number(r.mass_extinction_coefficient_m2_kg),tau=Number(iwp)*k;out.bands[String(wl)]={k_ext_m2_kg:k,tau,transmission:Math.exp(-tau),ssa:Number(r.single_scattering_albedo),g:Number(r.asymmetry_parameter),source_effective_radius_um:Number(r.effective_radius_um)};}
  return out;
}
