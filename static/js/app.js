document.addEventListener("DOMContentLoaded", () => {
    const deleteForms = document.querySelectorAll(".delete-request-form");

    deleteForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const requestName = form.dataset.requestName;
            const confirmed = window.confirm(
                `Excluir a solicitação de ${requestName}? Esta ação não pode ser desfeita.`,
            );

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    const equipmentInputs = document.querySelectorAll('input[name="equipamentos"]');
    const equipmentOptions = document.querySelectorAll("[data-equipment-id]");
    const selectionCount = document.querySelector("#equipment-selection-count");

    if (equipmentInputs.length === 0 || equipmentOptions.length === 0) {
        return;
    }

    const updateSelectedEquipment = () => {
        const selectedIds = new Set(
            [...equipmentInputs]
                .filter((input) => input.checked)
                .map((input) => input.value),
        );

        equipmentOptions.forEach((option) => {
            const selected = selectedIds.has(option.dataset.equipmentId);
            option.classList.toggle("is-selected", selected);
        });

        if (selectionCount) {
            const total = selectedIds.size;
            selectionCount.textContent = `${total} ${total === 1 ? "selecionado" : "selecionados"}`;
        }
    };

    equipmentInputs.forEach((input) => {
        input.addEventListener("change", updateSelectedEquipment);
    });
    updateSelectedEquipment();
});
