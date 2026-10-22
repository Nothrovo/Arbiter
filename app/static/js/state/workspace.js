export async function probeConnection(getHealth,lastSuccess){
  try{
    const health=await getHealth();
    if(health?.status!=='ok')throw new Error('Unverified status');
    return {state:'online',lastSuccess:new Date(),label:'Terhubung · lokal'};
  }catch{return {state:'offline',lastSuccess,label:'Tidak terhubung'};}
}
