// 移动端导航展开/收起
const header = document.querySelector(".site-header");
const navToggle = document.querySelector(".nav-toggle");

if (navToggle && header) {
  navToggle.addEventListener("click", () => {
    header.classList.toggle("nav-open");
  });
}

// 滚动进入视口的淡入动效
const animatedEls = document.querySelectorAll(".fade-up");

const io = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in-view");
        io.unobserve(entry.target);
      }
    });
  },
  {
    threshold: 0.1,
  },
);

animatedEls.forEach(el => io.observe(el));

// 数字自增动效
const counters = document.querySelectorAll(".count-up");

const counterObserver = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;

      const el = entry.target;
      const target = Number(el.getAttribute("data-target") || "0");
      const duration = 1200;
      const start = performance.now();

      const step = now => {
        const progress = Math.min((now - start) / duration, 1);
        const value = Math.floor(progress * target);
        el.textContent = value.toString();
        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          el.textContent = `${target}`;
        }
      };

      requestAnimationFrame(step);
      counterObserver.unobserve(el);
    });
  },
  { threshold: 0.3 },
);

counters.forEach(el => counterObserver.observe(el));

// 页脚年份
const yearEl = document.getElementById("year");
if (yearEl) {
  yearEl.textContent = new Date().getFullYear().toString();
}

