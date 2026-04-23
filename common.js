/* ── Star Canvas ── */
function initStars() {
  const canvas = document.getElementById('star-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W = canvas.width = window.innerWidth;
  let H = canvas.height = window.innerHeight;
  window.addEventListener('resize', () => {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });

  const STAR_COUNT = 280;
  const stars = Array.from({ length: STAR_COUNT }, () => ({
    x: Math.random() * W, y: Math.random() * H,
    r: Math.random() * 1.4 + 0.2,
    a: Math.random(),
    da: (Math.random() - 0.5) * 0.006,
    speed: Math.random() * 0.04,
    color: Math.random() < 0.08 ? '#818cf8' : Math.random() < 0.05 ? '#22d3ee' : '#ffffff'
  }));

  // Occasional shooting star
  let shoots = [];
  setInterval(() => {
    if (Math.random() < 0.3) {
      shoots.push({
        x: Math.random() * W * 0.7,
        y: Math.random() * H * 0.4,
        len: 80 + Math.random() * 120,
        speed: 6 + Math.random() * 6,
        a: 1
      });
    }
  }, 3000);

  function draw() {
    ctx.clearRect(0, 0, W, H);
    stars.forEach(s => {
      s.a += s.da;
      if (s.a <= 0 || s.a >= 1) s.da *= -1;
      ctx.globalAlpha = Math.max(0, Math.min(1, s.a));
      ctx.fillStyle = s.color;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
      // Glow for special stars
      if (s.color !== '#ffffff') {
        ctx.globalAlpha = s.a * 0.25;
        ctx.shadowBlur = 10;
        ctx.shadowColor = s.color;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r * 2.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    });

    // Shooting stars
    shoots = shoots.filter(sh => sh.a > 0);
    shoots.forEach(sh => {
      ctx.globalAlpha = sh.a * 0.8;
      const grad = ctx.createLinearGradient(sh.x, sh.y, sh.x + sh.len, sh.y + sh.len * 0.4);
      grad.addColorStop(0, 'rgba(255,255,255,0)');
      grad.addColorStop(1, 'rgba(255,255,255,1)');
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(sh.x, sh.y);
      ctx.lineTo(sh.x + sh.len, sh.y + sh.len * 0.4);
      ctx.stroke();
      sh.x += sh.speed;
      sh.y += sh.speed * 0.4;
      sh.a -= 0.025;
    });

    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }
  draw();
}

/* ── Tab Switch ── */
function switchTab(tabId, btn) {
  const section = btn.closest('.tab-section');
  section.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  section.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  btn.classList.add('active');
}

/* ── Slider ── */
function updateSlider(id, suffix) {
  const el = document.getElementById(id);
  const out = document.getElementById(id + '_val');
  if (out) out.textContent = el.value + (suffix || '');
}

/* ── AI Run ── */
function runAI(outputId, messages) {
  const out = document.getElementById(outputId);
  out.innerHTML = '<span class="ai-loading">◈ INITIALIZING NEURAL ENGINE ...</span>';
  out.style.display = 'block';
  let i = 0;
  out.innerHTML = '';
  const iv = setInterval(() => {
    if (i < messages.length) {
      const div = document.createElement('div');
      div.className = 'ai-result-item';
      div.textContent = messages[i];
      div.style.opacity = '0';
      div.style.transform = 'translateY(4px)';
      out.appendChild(div);
      requestAnimationFrame(() => {
        div.style.transition = 'opacity 0.3s, transform 0.3s';
        div.style.opacity = '1';
        div.style.transform = 'translateY(0)';
      });
      i++;
    } else clearInterval(iv);
  }, 480);
}

/* ── File Upload ── */
function handleUpload(inputId, previewId) {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  preview.innerHTML = '';
  Array.from(input.files).forEach(f => {
    const chip = document.createElement('div');
    chip.className = 'file-chip';
    chip.innerHTML = '◈ ' + f.name + ' <span style="color:var(--text-muted);margin-left:4px">(' + (f.size / 1024).toFixed(1) + ' KB)</span>';
    preview.appendChild(chip);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initStars();
});
