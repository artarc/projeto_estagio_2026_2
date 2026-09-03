document.addEventListener("DOMContentLoaded", () => {
    const equipmentSelect = document.querySelector("#id_equipamento");
    const equipmentButtons = document.querySelectorAll("[data-equipment-id]");

    if (!equipmentSelect || equipmentButtons.length === 0) {
        return;
    }

    const updateSelectedEquipment = () => {
        equipmentButtons.forEach((button) => {
            const selected = button.dataset.equipmentId === equipmentSelect.value;
            button.classList.toggle("is-selected", selected);
            button.setAttribute("aria-pressed", String(selected));
        });
    };

    equipmentButtons.forEach((button) => {
        button.addEventListener("click", () => {
            equipmentSelect.value = button.dataset.equipmentId;
            equipmentSelect.dispatchEvent(new Event("change", { bubbles: true }));
            document.querySelector("#solicitar")?.scrollIntoView({ behavior: "smooth" });
            window.setTimeout(() => equipmentSelect.focus(), 450);
        });
    });

    equipmentSelect.addEventListener("change", updateSelectedEquipment);
    updateSelectedEquipment();
});

