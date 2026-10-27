import {tenantScope, tenantValues} from './scope.js';
import {withParams} from '../router.js';

const paramsForScope = scope => {
  const params = new URLSearchParams();
  for (const tenant of tenantValues(scope instanceof URLSearchParams ? scope : {tenant: scope})) params.append('tenant', tenant);
  return params;
};
const scopeKey = scope => tenantScope(scope instanceof URLSearchParams ? scope : {tenant: scope}).key;

export function createNavigationMemory(){
 const values=new Map();
 return {
  remember(route){
   if(route.page!=='triage')return;
   const original=new URLSearchParams(route.params);original.delete('alert');
   const canonical=paramsForScope(original);const params=new URLSearchParams(canonical);
   for(const [key,value] of original) if(key!=='tenant') params.append(key,value);
   values.set(scopeKey(canonical),params.toString());
  },
  destination(page,scope='all'){
   const key=scopeKey(scope);
   const params=page==='triage'&&values.has(key)?new URLSearchParams(values.get(key)):paramsForScope(scope);
   return withParams('/'+page,params);
  },
 };
}
