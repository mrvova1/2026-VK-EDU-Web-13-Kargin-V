import { Centrifuge } from 'centrifuge';

let centrifuge = null;
let currentQuestionId = null;

export function initCentrifugo(questionId, token) {
    if (centrifuge) centrifuge.disconnect();
    currentQuestionId = questionId;
    centrifuge = new Centrifuge('ws://localhost:8001/connection', {
        token: token,
    });
    centrifuge.on('connecting', function() { console.log('connecting'); });
    centrifuge.on('connect', function() { console.log('connected'); });
    centrifuge.on('error', function(e) { console.error(e); });
    
    const channel = `questions:${questionId}`;
    const sub = centrifuge.newSubscription(channel);
    sub.on('publication', function(ctx) {
        handleNewAnswer(ctx.data);
    });
    sub.subscribe();
    centrifuge.connect();
}

function handleNewAnswer(data) {
    const currentPage = getCurrentPageNumber();
    if (currentPage === 1) {
        prependAnswer(data);
    } else {
        alert('Появился новый ответ! Перейдите на первую страницу, чтобы увидеть его.');
    }
}

function getCurrentPageNumber() {
    const urlParams = new URLSearchParams(window.location.search);
    return parseInt(urlParams.get('page') || '1');
}

function prependAnswer(answerData) {
    const answersContainer = document.querySelector('.answers_box');
    const newAnswerHtml = renderAnswerCard(answerData);
    answersContainer.insertAdjacentHTML('afterbegin', newAnswerHtml);
    updateAnswersCount(+1);
}