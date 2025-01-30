document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("quizForm")
    const originalInput = document.getElementById("answer")

    // ランダムな文字列を生成する関数
    function generateRandomString(length) {
        const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        let result = ""
        for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length))
        }
        return result
    }

    // 新しい入力フィールドを生成
    const newInput = document.createElement("input")
    newInput.type = "text"
    newInput.name = "answer_" + generateRandomString(12) + "_" + Date.now()
    newInput.id = "dynamicAnswer"
    newInput.className = originalInput.className
    newInput.required = true
    newInput.autocomplete = "off"

    // 元の入力フィールドを新しいものに置き換え
    originalInput.parentNode.replaceChild(newInput, originalInput)

    // フォーム送信時の処理
    form.addEventListener("submit", (e) => {
        e.preventDefault()
        const answerInput = document.getElementById("dynamicAnswer")
        const hiddenInput = document.createElement("input")
        hiddenInput.type = "hidden"
        hiddenInput.name = "answer"
        hiddenInput.value = answerInput.value
        form.appendChild(hiddenInput)
        form.submit()
    })
})