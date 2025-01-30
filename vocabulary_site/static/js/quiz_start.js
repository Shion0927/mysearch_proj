document.addEventListener("DOMContentLoaded", () => {
    const languageSelect = document.getElementById("language")
    const numQuestionsInput = document.getElementById("num_questions")
    const form = document.getElementById("quizForm")

    function updateMaxQuestions() {
        const selectedOption = languageSelect.options[languageSelect.selectedIndex]
        const wordCount = selectedOption.dataset.wordCount

        numQuestionsInput.max = wordCount
        numQuestionsInput.value = Math.min(numQuestionsInput.value, wordCount)
    }

    languageSelect.addEventListener("change", updateMaxQuestions)

    form.addEventListener("submit", (e) => {
        updateMaxQuestions()
        if (Number.parseInt(numQuestionsInput.value) > Number.parseInt(numQuestionsInput.max)) {
            e.preventDefault()
            alert("問題数が選択した言語の単語数を超えています。")
        }
    })

    // 初期化時にも実行
    updateMaxQuestions()
})

