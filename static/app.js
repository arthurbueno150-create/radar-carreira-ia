'use strict';
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num = (v, digits=0) => Number(v).toLocaleString('pt-BR', {maximumFractionDigits:digits, minimumFractionDigits:digits});
const date = s => s ? new Date(s).toLocaleDateString('pt-BR') : 'Não informada';
const state = {view:'overview', overview:null, extras:[], result:null, profile:'', loading:false, request:0, recommendRequest:0, cluster:null};
const colors = ['#416b39','#a3bc58','#517b92','#c49c52','#9073a2','#62a591'];
const pages = {
  overview:['Visão geral','O mercado, em perspectiva.','Explore competências, conecte oportunidades e planeje seu próximo passo.'],
  radar:['Meu radar','Seu repertório. Novas possibilidades.','Descubra conexões com vagas reais e simule o impacto de aprender algo novo.'],
  lab:['Laboratório ML','Por dentro da inteligência.','Método, avaliação e limites: ciência de dados que você consegue explicar.'],
  sources:['Sobre os dados','Antes do modelo, os dados.','Entenda de onde vem a amostra e como interpretar suas oportunidades.']
};
const presets = {
  data:'Tenho conhecimentos de Python, SQL e Pandas. Faço análise de dados e visualização de dados com Power BI. Uso essas competências em projetos de estudo.',
  ml:'Trabalho com Python, SQL, machine learning, scikit-learn e estatística. Uso PyTorch para deep learning e Git para versionar meus projetos.',
  dev:'Desenvolvo aplicações com JavaScript, TypeScript, React, Node.js, APIs e SQL. Uso Git, Docker e AWS em projetos de software.'
};
function filters(){return new URLSearchParams({category:$('#category').value,q:$('#search').value,location:$('#location').value});}
function fail(message){$('#error-banner').textContent=message;$('#error-banner').hidden=false;}
function clearError(){$('#error-banner').hidden=true;}
async function api(url, options){const response=await fetch(url,options); const data=await response.json(); if(!response.ok)throw new Error(data.error||'Não foi possível carregar os dados.'); return data;}
function setView(view){
  if(!pages[view])return;
  state.view=view;
  $$('.view').forEach(el=>el.hidden=el.id!==`view-${view}`);
  $$('.nav-item').forEach(el=>{el.classList.toggle('active',el.dataset.view===view); if(el.dataset.view===view)el.setAttribute('aria-current','page'); else el.removeAttribute('aria-current');});
  $('#breadcrumb').textContent=pages[view][0];$('#page-title').textContent=pages[view][1];$('#page-intro').textContent=pages[view][2];
  $('.heading-action').hidden=view!=='overview';$('#filterbar').hidden=['lab','sources'].includes(view);
  if(view==='lab')loadLab();
  if(view==='sources' && state.overview)renderSources(state.overview);
}
document.addEventListener('click',e=>{const button=e.target.closest('[data-view]');if(button){setView(button.dataset.view);window.scrollTo({top:0,behavior:'instant'});}});
function miniChart(data, count){return Object.entries(data).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([name,n])=>`<div class="mini-row"><div class="mini-row-label"><span>${escapeHtml(name)}</span><span>${num(n)}</span></div><div class="mini-track"><div class="mini-fill" style="width:${count ? n/count*100:0}%"></div></div></div>`).join('')||'<p class="input-note">Sem vagas neste filtro.</p>';}
function renderOverview(d){
  const stats=[['Vagas na amostra',num(d.count),'Anúncios após os filtros','▤'],['Empresas',num(d.companies),'Organizações diferentes','◈'],['Competências',num(d.skill_count),'Reconhecidas no vocabulário','⌘'],['Menções a IA',num(d.ai_share,1)+'%',`${num(d.ai_count)} vagas mencionam IA / ML`,'✳']];
  $('#stats').innerHTML=stats.map(([label,value,note,icon])=>`<article class="stat"><span class="stat-icon" aria-hidden="true">${icon}</span><p class="stat-label">${label}</p><div class="stat-value">${value}</div><p class="stat-note">${note}</p></article>`).join('');
  $('#snapshot-status').textContent=`Coleta em ${date(d.metadata.fetched_at)} · ${num(d.metadata.count)} vagas na base${d.age_days>7?' · Base com mais de 7 dias':''}`;
  const max=d.skills[0]?.count||1;
  $('#skill-chart').innerHTML=d.skills.slice(0,10).map(s=>`<button class="bar-row" data-filter-skill="${escapeHtml(s.name)}" title="${num(s.count)} de ${num(d.count)} vagas; ${num(s.share,1)}% da amostra"><span class="bar-name">${escapeHtml(s.name)}</span><span class="bar-track"><span class="bar-fill" style="display:block;width:${s.count/max*100}%"></span></span><span class="bar-value">${num(s.share,1)}%</span></button>`).join('')||'<p class="empty-chart">Nenhuma vaga encontrada. Tente limpar os filtros.</p>';
  $$('[data-filter-skill]').forEach(button=>button.addEventListener('click',()=>{$('#search').value=button.dataset.filterSkill;refresh();}));
  $('#category-chart').innerHTML=miniChart(d.categories,d.count);$('#location-chart').innerHTML=miniChart(d.locations,d.count);
  if(d.skills.length){$('#insight-title').textContent=`${d.skills[0].name} aparece em ${num(d.skills[0].count)} vagas desta amostra.`;$('#insight-text').textContent='Descubra quais competências se conectam às que você já conhece.';}
  else{$('#insight-title').textContent='Nenhuma vaga neste recorte.';$('#insight-text').textContent='Amplie a busca ou remova os filtros para continuar.';}
  renderMap(d);
}
function renderMap(d){
  const pts=d.points;
  if(!pts.length){$('#cluster-map').innerHTML='<p class="empty-chart">Sem pontos para os filtros selecionados.</p>';$('#cluster-legend').innerHTML='';return;}
  const xs=pts.map(p=>p.x),ys=pts.map(p=>p.y),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
  const x=v=>30+(v-xmin)/(xmax-xmin||1)*460,y=v=>230-(v-ymin)/(ymax-ymin||1)*205;
  const grid=[60,110,160,210].map(v=>`<line x1="22" y1="${v}" x2="508" y2="${v}" stroke="#edf1e8" stroke-dasharray="3 5"/>`).join('');
  $('#cluster-map').innerHTML=`<svg viewBox="0 0 530 260" role="img" aria-label="Projeção em duas dimensões de ${pts.length} vagas, agrupadas por competências">${grid}${pts.map(p=>`<circle cx="${x(p.x)}" cy="${y(p.y)}" r="4.4" fill="${p.cluster<0?'#aab6a2':colors[p.cluster%colors.length]}" style="opacity:${state.cluster===null||state.cluster===p.cluster?.78:.08}" tabindex="0"><title>${escapeHtml(p.title)} · ${escapeHtml(p.company)}</title></circle>`).join('')}</svg>`;
  const counts={};pts.forEach(p=>counts[p.cluster]=(counts[p.cluster]||0)+1);
  $('#cluster-legend').innerHTML=d.clusters.filter(c=>counts[c.id]).map(c=>`<button class="legend-button ${state.cluster!==null&&state.cluster!==c.id?'dim':''}" data-cluster="${c.id}" aria-pressed="${state.cluster===c.id}" title="Destacar grupo: ${escapeHtml(c.name)}"><span class="legend-dot" style="background:${c.id<0?'#aab6a2':colors[c.id%colors.length]}"></span>${escapeHtml(c.name)} <span>(${counts[c.id]})</span></button>`).join('');
  $$('[data-cluster]').forEach(b=>b.addEventListener('click',()=>{state.cluster=state.cluster===Number(b.dataset.cluster)?null:Number(b.dataset.cluster);renderMap(d);}));
}
async function refresh(){
  const token=++state.request;
  $('#export-plan').disabled=true;
  try{clearError();const d=await api('/api/overview?'+filters());if(token!==state.request)return;state.overview=d;state.cluster=null;renderOverview(d);if(state.view==='sources')renderSources(d);if(state.result)await analyze(false);}
  catch(e){if(token===state.request)fail('Erro ao carregar a amostra: '+e.message);}
}
function renderExtras(){
  $('#extra-skills').innerHTML=state.extras.map(s=>`<button class="remove-skill" data-remove="${escapeHtml(s)}" title="Remover ${escapeHtml(s)} da simulação">${escapeHtml(s)} ×</button>`).join('');
  $$('[data-remove]').forEach(b=>b.addEventListener('click',()=>{state.extras=state.extras.filter(s=>s!==b.dataset.remove);renderExtras();if(state.result)analyze(false);}));
}
function addSkill(skill){if(!skill)return;if(state.result?.detected_skills.includes(skill)){fail('Essa competência já foi identificada no perfil. Escolha outra para simular.');return;}if(!state.extras.includes(skill))state.extras.push(skill);renderExtras();if(state.result)analyze(false);}
function pill(s,missing=false){return `<span class="skill-pill ${missing?'missing':''}">${escapeHtml(s)}</span>`;}
function renderRecommendations(r){
  $('#detected').innerHTML=`<p>Competências identificadas no perfil (${r.detected_skills.length})</p><div class="chips">${r.detected_skills.map(s=>pill(s)).join('')||'<p class="input-note">Nenhuma competência do vocabulário foi reconhecida. Experimente termos como Python, SQL ou machine learning.</p>'}</div>`;
  $('#recommendation-status').textContent=r.total?`${num(r.total)} vagas no recorte · exibindo as ${r.matches.length} primeiras por afinidade${r.has_text_signal?'':' · perfil sem termos reconhecidos pelo modelo de texto'}`:'Nenhuma vaga corresponde aos filtros. Limpe ou amplie a busca.';
  $('#job-list').innerHTML=r.matches.map(j=>`<article class="job-card"><div class="job-top"><div><p class="company">${escapeHtml(j.company)}</p><h3>${escapeHtml(j.title)}</h3></div><div class="affinity">${num(j.score,1)}<small>afinidade / 100</small></div></div><div class="job-meta"><span>${escapeHtml(j.location)}</span><span>${escapeHtml(j.level)}</span><span>${escapeHtml(j.category)}</span></div><div class="match-explanation"><span>Cobertura de skills <strong>${num(j.coverage,1)}%</strong></span><span>Similaridade textual <strong>${num(j.text_similarity,1)}%</strong></span></div><div class="chips">${j.matched.map(s=>pill(s)).join('')}${j.missing.slice(0,6).map(s=>pill(s,true)).join('')}${j.missing.length>6?`<span class="skill-pill missing">+${j.missing.length-6} não cobertas</span>`:''}${!j.skills.length?'<span class="input-note">Sem competências reconhecidas; ranking baseado no texto.</span>':''}</div><details><summary>Entender esta recomendação</summary><p class="job-description">Verde: competências presentes no seu perfil ou na simulação. Cinza: mencionadas na vaga e ainda não cobertas. A cobertura pondera competências menos frequentes com peso maior. Não considera fluência, tempo de experiência ou elegibilidade geográfica.</p>${j.missing.length?`<p class="job-description"><strong>Competências não cobertas:</strong> ${j.missing.map(escapeHtml).join(', ')}.</p>`:''}<p class="job-description">${escapeHtml(j.description)}${j.description.length>=1200?'…':''}</p></details><div class="job-bottom"><span>Fonte: Jobicy · ${date(j.published_at)}</span><a href="${escapeHtml(j.url)}" target="_blank" rel="noopener noreferrer">Ver anúncio original ↗</a></div></article>`).join('')||'<div class="empty-state"><span>⌕</span><h3>Nenhuma conexão neste recorte.</h3><p>Remova os filtros para explorar outras oportunidades.</p></div>';
  const s=r.simulation,gain=s.after-s.before;
  $('#simulation').innerHTML=`<div class="simulation-numbers"><div><span>${num(s.before,1)}%</span><small>cobertura atual</small></div><span>→</span><div><strong>${num(s.after,1)}%</strong><small>com a simulação</small></div></div><p class="simulation-gain">+${num(Math.max(0,gain),1)} pontos percentuais de cobertura média</p><p class="input-note">${num(s.above80_before)} → ${num(s.above80_after)} vagas com cobertura de pelo menos 80%. Média de ${num(r.assessed)} vagas com competências extraídas. Não indica chance de contratação.</p>`;
  $('#learning-section').hidden=!r.plan.length;
  $('#learning-plan').innerHTML=r.plan.map((p,i)=>`<article class="learning-item"><span class="learning-number">PRÓXIMO PASSO ${String(i+1).padStart(2,'0')}</span><h3>${escapeHtml(p.skill)}</h3><div class="learning-gain">+${num(p.gain,2)} p.p. · presente em ${p.jobs} vagas</div><p>${escapeHtml(p.task)}</p>${p.url?`<a href="${escapeHtml(p.url)}" target="_blank" rel="noopener noreferrer">Documentação para começar ↗</a>`:''}<button data-learn="${escapeHtml(p.skill)}">Simular esta competência +</button></article>`).join('');
  $$('[data-learn]').forEach(b=>b.addEventListener('click',()=>{addSkill(b.dataset.learn);$('.simulation-card').scrollIntoView({behavior:'smooth',block:'center'});}));
}
async function analyze(fromButton=true){
  const profile=$('#profile').value.trim();
  if(!profile){fail('Descreva suas competências antes de analisar.');$('#profile').focus();return;}
  const token=++state.recommendRequest;
  $('#analyze').disabled=true;$('#export-plan').disabled=true;$('#analyze').textContent='Analisando em Python…';
  try{clearError();const r=await api('/api/recommend?'+filters(),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile,extra_skills:state.extras})});if(token!==state.recommendRequest)return;state.profile=profile;state.result=r;state.extras=r.extra_skills;renderExtras();renderRecommendations(r);$('#export-plan').disabled=false;}
  catch(e){if(token===state.recommendRequest)fail(e.message);}
  finally{if(token===state.recommendRequest){$('#analyze').disabled=false;$('#analyze').innerHTML='Encontrar conexões <span>↗</span>';}}
}
async function loadLab(){
  try{const d=await api('/api/methodology');const s=d.report.supervised;
    $('#lab-content').innerHTML=`<div class="lab-grid"><section class="card"><p class="eyebrow">MODELO 01 / RECOMENDAÇÃO</p><h2>Afinidade que você pode inspecionar</h2><div class="model-pipeline"><span>Texto</span>→<span>TF-IDF</span>→<span>Cosseno</span></div><p class="lab-detail">O TF-IDF aprende a importância de termos em ${num(d.metadata.count)} anúncios. O perfil é comparado às vagas por similaridade do cosseno. Um componente adicional mede a cobertura das competências citadas, ponderada pela raridade na base.</p><p class="notice">Índice = 0,65 × cobertura + 0,35 × similaridade textual. Pesos definidos para este protótipo; não calibrados com contratações reais. O reconhecimento de ${d.skills} competências usa um dicionário de regras.</p><p class="info-line">${num(d.vocabulary)} termos e pares de palavras no vocabulário aprendido.</p></section><section class="card"><p class="eyebrow">MODELO 02 / DESCOBERTA DE GRUPOS</p><h2>K-means com escolha de k</h2><p class="lab-detail">As competências recebem pesos IDF e normalização L2. Comparamos de 2 a 6 grupos e escolhemos o maior silhouette por distância do cosseno, na própria amostra. A projeção SVD serve apenas para visualização.</p><table class="simple-table"><thead><tr><th>Grupos (k)</th><th>Silhouette</th></tr></thead><tbody>${d.trials.map(t=>`<tr><td>${t.k}</td><td>${num(t.silhouette,4)}${t.silhouette===d.silhouette?' · selecionado':''}</td></tr>`).join('')}</tbody></table><p class="input-note">Valores próximos de zero sugerem sobreposição. Não é acurácia nem avaliação em dados futuros. A projeção 2D retém ${num(d.projection_variance*100,1)}% da variância.</p></section></div>${s?.model?`<section class="card" style="margin-top:20px"><p class="eyebrow">EXPERIMENTO AUXILIAR / CLASSIFICAÇÃO SUPERVISIONADA</p><h2>O texto distingue as categorias da fonte?</h2><p class="card-sub">TF-IDF + regressão logística versus uma regra que sempre prevê a categoria mais frequente.</p><div class="lab-grid"><div><div class="metric-compare"><div class="metric-box"><span>${num(s.model.macro_f1,3)}</span><p>Macro-F1 · modelo</p><small>Acurácia: ${num(s.model.accuracy*100,1)}%</small></div><div class="metric-box"><span>${num(s.baseline.macro_f1,3)}</span><p>Macro-F1 · baseline</p><small>Acurácia: ${num(s.baseline.accuracy*100,1)}%</small></div></div><p class="lab-detail">Treino: <strong>${s.train_rows} vagas / ${s.train_companies} empresas</strong>.<br>Teste: <strong>${s.test_rows} vagas / ${s.test_companies} empresas</strong>.<br>Empresas presentes nos dois conjuntos: <strong>${s.company_overlap}</strong>.<br>Vocabulário do experimento ajustado somente no treino.</p></div><div><h3 style="margin-top:20px">Matriz de confusão</h3><p class="input-note">Linhas: categoria real da fonte · colunas: previsão.</p><div class="table-scroll"><table class="simple-table"><thead><tr><th>Real / prevista</th>${s.classes.map(c=>`<th>${escapeHtml(c)}</th>`).join('')}</tr></thead><tbody>${s.confusion_matrix.map((row,i)=>`<tr><th>${escapeHtml(s.classes[i])}</th>${row.map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table></div></div></div><p class="notice">${escapeHtml(s.limitations)} A classificação é um experimento didático separado; ela não produz o ranking de vagas.</p></section>`:`<div class="notice">${escapeHtml(d.report.status||'Relatório indisponível. Execute python train.py.')}</div>`}<p class="info-line">Experimentos reproduzíveis com random_state=42. Código, notebook e relatório JSON acompanham o projeto.</p>`;
  }catch(e){fail(e.message);}
}
function renderSources(d){const m=d.metadata;
  $('#sources-content').innerHTML=`<div class="source-grid"><section class="card"><p class="eyebrow">ORIGEM E RASTREABILIDADE</p><h2>Uma amostra real, com contexto.</h2><p>Os anúncios vêm da API pública do <a href="https://jobicy.com/jobs-rss-feed" target="_blank" rel="noopener noreferrer">Jobicy</a>. A coleta consulta até 200 vagas recentes de cada uma das categorias Data Science & Analytics e Software Engineering.</p><div class="data-field"><span>Coleta (horário local)</span><strong>${new Date(m.fetched_at).toLocaleString('pt-BR')}</strong></div><div class="data-field"><span>Anúncios recebidos → base tratada</span><strong>${num(m.raw_count)} → ${num(m.count)} vagas</strong></div><div class="data-field"><span>Deduplicação e qualidade</span><strong>${m.duplicates_removed} duplicatas removidas · ${m.rejected} registros rejeitados</strong></div><div class="data-field"><span>Integridade da base (SHA-256)</span><code>${escapeHtml(m.sha256)}</code></div><p class="notice">${escapeHtml(m.sampling)} A disponibilidade de cada anúncio pode mudar após a coleta. Consulte sempre a página original.</p></section><section class="card"><p class="eyebrow">LEIA ANTES DE INTERPRETAR</p><h2>O que os dados não dizem</h2><ul><li>Uma menção não significa requisito obrigatório. O extrator também encontra tecnologias citadas como diferenciais ou contexto.</li><li>A amostra privilegia trabalho remoto internacional e anúncios em inglês. Ela não representa todo o mercado nem as vagas brasileiras.</li><li>Competências frequentes nesta coleta não demonstram crescimento ao longo do tempo. Não há série histórica de demanda.</li><li>Afinidade e cobertura não medem sua proficiência, senioridade ou chance de contratação.</li><li>O vocabulário é limitado. Negações como “não conheço Python” ainda podem ser contadas como menções. Informe apenas o que você sabe.</li><li>Salários incompletos ou em moedas diferentes não são comparados neste projeto.</li></ul></section><section class="card"><p class="eyebrow">ATUALIZAÇÃO MANUAL</p><h2>Reproduzir e renovar a amostra</h2><p>O aplicativo funciona com a base local incluída. Para atualizar, execute <code>python collect.py</code>, depois <code>python train.py</code> e reinicie o servidor. A coleta respeita um intervalo mínimo de seis horas e preserva a última base válida em caso de falha.</p><p class="notice">A avaliação é vinculada ao hash da base. Quando os dados mudam, métricas antigas deixam de aparecer até que o experimento seja refeito.</p></section><section class="card"><p class="eyebrow">SEU PERFIL</p><h2>Sem cadastro ou armazenamento de perfil.</h2><p>O texto informado é enviado apenas ao servidor deste aplicativo. O código não grava o perfil em banco de dados, arquivos ou logs, e não usa serviços de IA externos. Evite incluir informações pessoais: uma lista de competências é suficiente.</p><p style="margin-top:15px">A exportação inclui competências reconhecidas, simulação, recomendações e origem dos dados. O texto completo do perfil não é incluído.</p></section></div>`;
}
let searchTimer;
$('#search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(refresh,300);});
$('#category').addEventListener('change',refresh);$('#location').addEventListener('change',refresh);
$('#clear-filters').addEventListener('click',()=>{$('#search').value='';$('#category').value='';$('#location').value='';refresh();});
$('#analyze').addEventListener('click',()=>analyze());
$$('[data-preset]').forEach(b=>b.addEventListener('click',()=>{$('#profile').value=presets[b.dataset.preset];state.extras=[];renderExtras();analyze();}));
$('#profile').addEventListener('input',()=>{if(state.result){$('#export-plan').disabled=true;$('#recommendation-status').textContent='Perfil editado. Clique em “Encontrar conexões” para atualizar os resultados.';}});
$('#add-skill').addEventListener('click',()=>{addSkill($('#new-skill').value);$('#new-skill').value='';});
$('#export-plan').addEventListener('click',async()=>{
  try{const response=await fetch('/api/export?'+filters(),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile:state.profile,extra_skills:state.extras})});if(!response.ok)throw new Error('Não foi possível exportar o plano.');const blob=await response.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='meu-plano-radar.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  catch(e){fail(e.message);}
});
async function init(){try{const options=await api('/api/options');options.categories.forEach(s=>$('#category').add(new Option(s,s)));options.locations.forEach(s=>$('#location').add(new Option(s,s)));options.skills.forEach(s=>$('#new-skill').add(new Option(s,s)));await refresh();}catch(e){fail('O servidor não respondeu: '+e.message);}}
init();
