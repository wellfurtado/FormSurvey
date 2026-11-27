// JavaScript do FormSurvey. Mantive o mínimo possível: o sistema funciona
// inteiro sem JavaScript (formulários e links comuns); o que está aqui só
// melhora a experiência. Sem bibliotecas externas.

// 1) Animação de entrada: elementos com a classe ".fade-in" aparecem
//    suavemente quando entram na tela. Se o navegador não tiver
//    IntersectionObserver, eu mostro tudo de uma vez.
(() => {
  const targets = document.querySelectorAll(".fade-in");
  if (!("IntersectionObserver" in window) || targets.length === 0) {
    targets.forEach((el) => el.classList.add("in-view"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  targets.forEach((el) => observer.observe(el));
})();

// 2) Botões "Copiar": um botão com data-copy="#campo" copia o valor do campo
//    (link do menor, link de retomada). Se a API de área de transferência não
//    estiver disponível (página sem HTTPS, por exemplo), uso o método antigo.
document.querySelectorAll("[data-copy]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const field = document.querySelector(btn.getAttribute("data-copy"));
    if (!field) return;
    try {
      await navigator.clipboard.writeText(field.value);
    } catch (err) {
      field.select();
      document.execCommand("copy");
    }
    const original = btn.textContent;
    btn.textContent = "Copiado!";
    setTimeout(() => { btn.textContent = original; }, 1500);
  });
});

// 3) Revelar ao clicar: um link com data-reveal="#bloco" mostra o bloco
//    escondido quando é clicado. Uso isso na etapa do chatbot: o botão do
//    questionário só aparece depois que "Abrir o chatbot" foi clicado. Quem
//    está sem JavaScript vê o botão ao recarregar a página, porque o servidor
//    já sabe que o chatbot foi aberto.
document.querySelectorAll("[data-reveal]").forEach((link) => {
  link.addEventListener("click", () => {
    const target = document.querySelector(link.getAttribute("data-reveal"));
    if (target) target.hidden = false;
  });
});
