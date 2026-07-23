(function() {
  function init(wrapper) {
    var zone = wrapper.querySelector('.drag-drop-zone');
    var input = wrapper.querySelector('input[type="file"]');
    if (!input) return;

    function preview() {
      if (!input.files || !input.files.length) return;
      var reader = new FileReader();
      reader.onload = function(e) {
        var img = wrapper.querySelector('.drag-drop-preview img') || document.createElement('img');
        img.src = e.target.result;
        img.style.cssText = 'max-height:100px;border-radius:6px;margin-top:6px;display:block;';
        var container = wrapper.querySelector('.drag-drop-preview');
        if (!container) {
          container = document.createElement('div');
          container.className = 'drag-drop-preview';
          container.style.cssText = 'margin-top:6px;position:relative;';
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.textContent = '\u00d7';
          btn.style.cssText = 'position:absolute;top:-6px;right:-6px;width:20px;height:20px;border-radius:50%;background:#EF4444;color:#fff;border:2px solid #fff;cursor:pointer;font-size:12px;line-height:0;padding:0;';
          btn.onclick = function(e) { e.stopPropagation(); input.value = ''; container.remove(); wrapper.querySelector('.drag-drop-zone').style.display = ''; };
          container.appendChild(btn);
          container.appendChild(img);
          wrapper.appendChild(container);
        }
        container.style.display = 'block';
        zone.style.display = 'none';
      };
      reader.readAsDataURL(input.files[0]);
    }

    input.addEventListener('change', preview);

    if (zone) {
      zone.addEventListener('dragover', function(e) { e.preventDefault(); zone.classList.add('drag-over'); });
      zone.addEventListener('dragleave', function(e) { e.preventDefault(); zone.classList.remove('drag-over'); });
    }
    input.addEventListener('dragover', function(e) { e.preventDefault(); if (zone) zone.classList.add('drag-over'); });
    input.addEventListener('dragleave', function(e) { e.preventDefault(); if (zone) zone.classList.remove('drag-over'); });
    input.addEventListener('drop', function(e) { if (zone) zone.classList.remove('drag-over'); });
  }

  document.querySelectorAll('.drag-drop-wrapper').forEach(init);
  new MutationObserver(function(muts) {
    muts.forEach(function(m) {
      m.addedNodes.forEach(function(n) {
        if (n.querySelectorAll) n.querySelectorAll('.drag-drop-wrapper:not([data-dd])').forEach(function(w) { w.dataset.dd = '1'; init(w); });
      });
    });
  }).observe(document.body, { childList: true, subtree: true });
})();
