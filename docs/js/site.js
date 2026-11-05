
(function(){
  if(/github\.io$/.test(location.hostname)){ document.querySelectorAll('a.out').forEach(function(a){a.remove()}); }
  document.querySelectorAll('.cmp').forEach(function(c){
    var r=c.querySelector('input[type=range]'), b=c.querySelector('.b'), h=c.querySelector('.hd');
    function set(v){ b.style.clipPath='inset(0 '+(100-v)+'% 0 0)'; h.style.left=v+'%'; }
    r.addEventListener('input',function(){set(+r.value)}); set(50);
  });
  var bar=document.getElementById('filters'); if(!bar) return;
  var units=document.querySelectorAll('#apx .apx-unit');
  var saved=null; try{saved=localStorage.getItem('amb-unit')}catch(e){}
  function apply(u){
    units.forEach(function(el){el.hidden = !(u==='all' || el.getAttribute('data-unit')===u)});
    bar.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed', b.getAttribute('data-unit')===u ? 'true':'false')});
    try{localStorage.setItem('amb-unit',u)}catch(e){}
  }
  bar.addEventListener('click',function(ev){var b=ev.target.closest('button'); if(!b) return; apply(b.getAttribute('data-unit'));});
  var h=(location.hash||'').replace('#',''); if(h && bar.querySelector('[data-unit="'+h+'"]')) apply(h);
  else if(saved && bar.querySelector('[data-unit="'+saved+'"]')) apply(saved);
})();
