(() => {
  "use strict";

  const replay = document.querySelector("#replay");
  if (!replay) return;

  const steps = replay.querySelector(".replay-steps");
  const buttons = [...steps.querySelectorAll("button")];
  const panels = buttons.map(button => document.getElementById(button.getAttribute("aria-controls")));
  const actions = replay.querySelector(".replay-actions");
  const progress = replay.querySelector(".replay-progress");
  const next = replay.querySelector("[data-replay-next]");
  let current = 0;

  function showStep(index) {
    current = index;
    buttons.forEach((button, i) => {
      if (i === index) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
      panels[i].hidden = i !== index;
    });
    progress.textContent = `Step ${index + 1} of ${panels.length}`;
    next.textContent = index === panels.length - 1 ? "Restart replay" : "Next step";
  }

  buttons.forEach((button, index) => button.addEventListener("click", () => showStep(index)));
  next.addEventListener("click", () => {
    showStep((current + 1) % panels.length);
    panels[current].querySelector("h3").focus();
  });

  showStep(0);
  steps.hidden = false;
  actions.hidden = false;
})();
