document.addEventListener("DOMContentLoaded", function () {
  // --- 1. ĐIỀU HƯỚNG CHUYỂN BƯỚC ---
  const steps = document.querySelectorAll(".step");
  const nextBtns = document.querySelectorAll(".next-btn");
  const prevBtns = document.querySelectorAll(".prev-btn");
  const progressBar = document.getElementById("progressBar");
  let currentStep = 0;

  // 12 bước = 6 câu hồ sơ + 6 câu mini-test chẩn đoán (khớp questionaire/page.tsx).
  const STEP_REQUIRED = [
    { name: 'target_score' },
    { name: 'target_major' },
    { name: 'exam_timing' },
    { name: 'section3_choice' },
    { name: 'study_time' },
    { name: 'self_weak' },   // checkbox — tối đa 2, tối thiểu 1
    { name: 'dq_ql_1' },
    { name: 'dq_ql_2' },
    { name: 'dq_qt_1' },
    { name: 'dq_qt_2' },
    { name: 'dq_kh_1' },
    { name: 'dq_kh_2' },
  ];

  function isStepAnswered(stepIndex) {
    const req = STEP_REQUIRED[stepIndex];
    if (!req) return true;
    const hasSelection = document.querySelectorAll(`input[name="${req.name}"]:checked`).length > 0;
    return req.optional ? true : hasSelection;
  }

  function updateNextBtn() {
    const activeStep = steps[currentStep];
    if (!activeStep) return;
    const nextBtn = activeStep.querySelector('.next-btn');
    if (!nextBtn) return;
    nextBtn.classList.toggle('locked', !isStepAnswered(currentStep));
  }

  function updateForm() {
    steps.forEach((step, index) => {
      step.classList.toggle("active", index === currentStep);
    });
    const progress = (currentStep / (steps.length - 1)) * 100;
    progressBar.style.width = progress + "%";
    updateNextBtn();
  }

  nextBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!isStepAnswered(currentStep)) {
        showStepError('Vui lòng trả lời câu hỏi này trước khi tiếp tục.');
        shakeQuestion();
        return;
      }
      if (currentStep < steps.length - 1) {
        currentStep++;
        updateForm();
      }
    });
  });

  prevBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (currentStep > 0) {
        currentStep--;
        updateForm();
      }
    });
  });

  updateForm();

  document.getElementById("surveyForm").addEventListener("change", updateNextBtn);
  document.getElementById("surveyForm").addEventListener("input", updateNextBtn);

  // --- 2. GIỚI HẠN CHỌN TỐI ĐA (self_weak: 2) ---
  function setupMaxCheck(name, max) {
    document.querySelectorAll(`input[name="${name}"]`).forEach((cb) => {
      cb.addEventListener("change", () => {
        if (document.querySelectorAll(`input[name="${name}"]:checked`).length > max) {
          cb.checked = false;
          alert(`Bạn chỉ được chọn tối đa ${max} mục!`);
        }
      });
    });
  }
  setupMaxCheck("self_weak", 2);

  // --- 3. VALIDATE TOÀN BỘ TRƯỚC KHI SUBMIT ---
  function validateAll() {
    for (let i = 0; i < steps.length; i++) {
      if (!isStepAnswered(i)) return i;
    }
    return -1;
  }

  function shakeQuestion() {
    const block = steps[currentStep].querySelector('.question-block');
    if (!block) return;
    block.classList.remove('shake');
    void block.offsetWidth;
    block.classList.add('shake');
    block.addEventListener('animationend', () => block.classList.remove('shake'), { once: true });
  }

  function showStepError(message) {
    const activeStep = steps[currentStep];
    let errEl = activeStep.querySelector('.step-error');
    if (!errEl) {
      errEl = document.createElement('p');
      errEl.className = 'step-error';
      activeStep.querySelector('.btn-group').before(errEl);
    }
    errEl.textContent = message;
    errEl.style.display = 'block';
    clearTimeout(errEl._hideTimer);
    errEl._hideTimer = setTimeout(() => { errEl.style.display = 'none'; }, 3000);
  }

  // --- 4. SUBMIT: gom dữ liệu → POST /api/survey ---
  document
    .getElementById("surveyForm")
    .addEventListener("submit", async function (event) {
      event.preventDefault();

      const failingStep = validateAll();
      if (failingStep !== -1) {
        currentStep = failingStep;
        updateForm();
        showStepError('Vui lòng hoàn thành câu hỏi này trước khi gửi.');
        return;
      }

      const formData = new FormData(this);
      const finalSurveyData = { self_weak: [] };
      for (const [key, value] of formData.entries()) {
        if (key === 'self_weak') {
          finalSurveyData.self_weak.push(value);
        } else {
          finalSurveyData[key] = value;
        }
      }
      finalSurveyData.self_weak = finalSurveyData.self_weak.join(", ");

      try {
        const res = await fetch("/api/survey", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify(finalSurveyData),
        });
        const data = await res.json();
        if (!res.ok) {
          let errMsg = "Không thể lưu khảo sát.";
          if (typeof data.error === 'string') errMsg = data.error;
          else if (data.error && typeof data.error === 'object' && data.error.message) errMsg = data.error.message;
          throw new Error(errMsg);
        }
        showThanksModal();
      } catch (err) {
        alert(err.message || "Không thể lưu khảo sát, vui lòng thử lại.");
      }
    });

  function showThanksModal() {
    const overlay = document.getElementById("thanksOverlay");
    const okBtn = document.getElementById("thanksOkBtn");
    if (!overlay || !okBtn) return;
    overlay.classList.add("show");
    overlay.setAttribute("aria-hidden", "false");
    okBtn.onclick = function () {
      window.location.href = "/dashboard";
    };
  }
});
