import {withParams} from '../router.js';
export function createNavigationMemory(){
 const values=new Map();
 return {
  remember(route){
   if(route.page!=='triage')return;
   const params=new URLSearchParams(route.params);params.delete('alert');
   values.set(params.get('tenant')||'all',params.toString());
  },
  destination(page,tenant='all'){
   const params=page==='triage'&&values.has(tenant)?new URLSearchParams(values.get(tenant)):new URLSearchParams({tenant});
   return withParams('/'+page,params);
  },
 };
}
