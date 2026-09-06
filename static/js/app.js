document.addEventListener("DOMContentLoaded", () => {
    const equipmentInputs = document.querySelectorAll('input[name="equipamentos"]');
    const equipmentButtons = document.querySelectorAll("[data-equipment-id]");
    const selectionCount = document.querySelector("#equipment-selection-count");

    if (equipmentInputs.length === 0 || equipmentButtons.length === 0) {
        return;
    }

    const updateSelectedEquipment = () => {
        const selectedIds = new Set(
            [...equipmentInputs]
                .filter((input) => input.checked)
                .map((input) => input.value),
        );

        equipmentButtons.forEach((button) => {
            const selected = selectedIds.has(button.dataset.equipmentId);
            button.classList.toggle("is-selected", selected);
            button.setAttribute("aria-pressed", String(selected));
        });

        if (selectionCount) {
            const total = selectedIds.size;
            selectionCount.textContent = `${total} ${total === 1 ? "equipamento selecionado" : "equipamentos selecionados"}`;
        }
    };

    equipmentButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const input = [...equipmentInputs].find(
                (item) => item.value === button.dataset.equipmentId,
            );
            if (!input) return;

            input.checked = !input.checked;
            input.dispatchEvent(new Event("change", { bubbles: true }));
        });
    });

    equipmentInputs.forEach((input) => {
        input.addEventListener("change", updateSelectedEquipment);
    });
    updateSelectedEquipment();
});
