function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  return parts.length === 2 ? parts.pop().split(';').shift() : '';
}

async function postJSON(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest',
    },
    body: new URLSearchParams(data),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.message || 'Request failed');
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

function updateRating(container, rating) {
  const ratingNode = container.querySelector('.js-rating');
  if (ratingNode) {
    ratingNode.textContent = String(rating);
  }
}

function setVoteState(container, activeType) {
  const likeBtn = container.querySelector('[data-vote-type="like"]');
  const dislikeBtn = container.querySelector('[data-vote-type="dislike"]');

  if (!likeBtn || !dislikeBtn) return;

  likeBtn.disabled = true;
  dislikeBtn.disabled = true;

  likeBtn.classList.remove('active-vote');
  dislikeBtn.classList.remove('active-vote');

  if (activeType === 'like') likeBtn.classList.add('active-vote');
  if (activeType === 'dislike') dislikeBtn.classList.add('active-vote');
}

document.addEventListener('click', async (event) => {
  const qBtn = event.target.closest('.js-question-vote');
  const aBtn = event.target.closest('.js-answer-vote');
  const cBtn = event.target.closest('.js-correct-answer');

  try {
    if (qBtn) {
      event.preventDefault();

      const container = qBtn.closest('[data-question-id]');
      const payload = await postJSON('/ajax/question-vote/', {
        question_id: qBtn.dataset.questionId,
        vote_type: qBtn.dataset.voteType,
      });

      updateRating(container, payload.rating);
      setVoteState(container, qBtn.dataset.voteType);
      return;
    }

    if (aBtn) {
      event.preventDefault();

      const container = aBtn.closest('[data-answer-id]');
      const payload = await postJSON('/ajax/answer-vote/', {
        answer_id: aBtn.dataset.answerId,
        vote_type: aBtn.dataset.voteType,
      });

      updateRating(container, payload.rating);
      setVoteState(container, aBtn.dataset.voteType);
      return;
    }

    if (cBtn) {
      event.preventDefault();

      const questionId = cBtn.dataset.questionId;
      const answerId = cBtn.dataset.answerId;
      const checked = cBtn.checked;

      const payload = await postJSON('/ajax/correct-answer/', {
        question_id: questionId,
        answer_id: answerId,
        checked: checked ? '1' : '0',
      });

      document
        .querySelectorAll(`.js-correct-answer[data-question-id="${questionId}"]`)
        .forEach((el) => {
          el.checked = false;
        });

      if (payload.is_correct) {
        cBtn.checked = true;
      }
    }
  } catch (error) {
    const payload = error.payload || {};
    if (error.status === 401 && payload.redirect_url) {
      window.location.href = payload.redirect_url;
      return;
    }
    alert(payload.message || 'Ошибка');
  }
});