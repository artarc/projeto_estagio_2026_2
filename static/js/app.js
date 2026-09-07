document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".delete-request-form").forEach((form) => {
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

    const requestForm = document.querySelector(".request-form");
    const equipmentOptions = [...document.querySelectorAll("[data-equipment-id]")];
    if (!requestForm || equipmentOptions.length === 0) {
        return;
    }

    const selectionCount = document.querySelector("#equipment-selection-count");
    const withdrawalInput = document.querySelector("#id_data_retirada");
    const returnInput = document.querySelector("#id_data_devolucao");
    const availabilityNotice = document.querySelector("#equipment-availability-notice");
    const noticeTitle = document.querySelector("#availability-notice-title");
    const noticeDescription = document.querySelector("#availability-notice-description");
    const suggestedDatesButton = document.querySelector("#use-suggested-dates");
    const submitButton = requestForm.querySelector('button[type="submit"]');
    const availabilityUrl = requestForm.dataset.availabilityUrl;
    let debounceTimer;
    let requestSequence = 0;
    let suggestedDates = suggestedDatesButton.dataset.withdrawalDate
        ? {
            withdrawal: suggestedDatesButton.dataset.withdrawalDate,
            return: suggestedDatesButton.dataset.returnDate,
        }
        : null;

    const getQuantityInput = (option) => option.querySelector(".equipment-quantity-input");
    const getCheckbox = (option) => option.querySelector(".equipment-checkbox");

    const clampQuantity = (option, value) => {
        const maximum = Number(option.dataset.totalQuantity);
        const parsedValue = Number.parseInt(value, 10);
        if (Number.isNaN(parsedValue)) {
            return 0;
        }
        return Math.min(Math.max(parsedValue, 0), maximum);
    };

    const getSelectedItems = () => equipmentOptions
        .map((option) => ({
            equipamento_id: Number(option.dataset.equipmentId),
            quantidade: clampQuantity(option, getQuantityInput(option).value),
        }))
        .filter((item) => item.quantidade > 0);

    const setCardStatus = (option, statusText, available) => {
        const status = option.querySelector("[data-equipment-status]");
        if (!status) {
            return;
        }
        status.textContent = statusText;
        status.classList.toggle("availability-available", available);
        status.classList.toggle("availability-unavailable", !available);
    };

    const resetCardStatuses = () => {
        equipmentOptions.forEach((option) => {
            const availableNow = Number(option.dataset.currentAvailable);
            option.classList.remove("is-period-unavailable");
            setCardStatus(
                option,
                availableNow > 0 ? "Disponível" : "Indisponível agora",
                availableNow > 0,
            );
        });
    };

    const showNotice = (variant, title, description, dates = null) => {
        suggestedDates = dates;
        availabilityNotice.classList.remove("is-hidden", "is-neutral", "is-success", "is-error");
        availabilityNotice.classList.add(`is-${variant}`);
        noticeTitle.textContent = title;
        noticeDescription.textContent = description;
        suggestedDatesButton.classList.toggle("is-hidden", !dates);
    };

    const hideNotice = () => {
        availabilityNotice.classList.add("is-hidden");
        suggestedDates = null;
    };

    const updateSelectedEquipment = () => {
        let totalUnits = 0;

        equipmentOptions.forEach((option) => {
            const quantityInput = getQuantityInput(option);
            const quantity = clampQuantity(option, quantityInput.value);
            const checkbox = getCheckbox(option);
            quantityInput.value = quantity;
            checkbox.checked = quantity > 0;
            option.classList.toggle("is-selected", quantity > 0);
            totalUnits += quantity;

            const decreaseButton = option.querySelector('[data-quantity-action="decrease"]');
            const increaseButton = option.querySelector('[data-quantity-action="increase"]');
            decreaseButton.disabled = quantity === 0;
            increaseButton.disabled = quantity >= Number(option.dataset.totalQuantity);
        });

        if (selectionCount) {
            selectionCount.textContent = `${totalUnits} ${totalUnits === 1 ? "unidade selecionada" : "unidades selecionadas"}`;
        }
    };

    const csrfToken = () => requestForm.querySelector('[name="csrfmiddlewaretoken"]').value;

    const formatDate = (value) => new Intl.DateTimeFormat("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        timeZone: "UTC",
    }).format(new Date(`${value}T00:00:00Z`));

    const checkAvailability = async () => {
        const items = getSelectedItems();
        const currentSequence = ++requestSequence;

        resetCardStatuses();
        if (items.length === 0) {
            hideNotice();
            submitButton.disabled = false;
            return;
        }

        if (!withdrawalInput.value || !returnInput.value) {
            showNotice(
                "neutral",
                "Informe o período do empréstimo",
                "As datas são necessárias para conferir se todas as quantidades estarão disponíveis.",
            );
            submitButton.disabled = false;
            return;
        }

        showNotice("neutral", "Consultando disponibilidade", "Estamos conferindo o estoque para o período escolhido.");

        try {
            const response = await fetch(availabilityUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken(),
                },
                body: JSON.stringify({
                    data_retirada: withdrawalInput.value,
                    data_devolucao: returnInput.value,
                    itens: items,
                }),
            });
            const data = await response.json();

            if (currentSequence !== requestSequence) {
                return;
            }
            if (!response.ok) {
                throw new Error(data.erro || "Não foi possível consultar a disponibilidade.");
            }

            data.itens.forEach((item) => {
                const option = equipmentOptions.find(
                    (candidate) => Number(candidate.dataset.equipmentId) === item.equipamento_id,
                );
                if (!option) {
                    return;
                }
                option.classList.toggle("is-period-unavailable", !item.disponivel);
                setCardStatus(
                    option,
                    item.disponivel
                        ? `${item.quantidade_disponivel} disponíveis no período`
                        : `Só ${item.quantidade_disponivel} disponíveis no período`,
                    item.disponivel,
                );
            });

            if (data.disponivel) {
                showNotice(
                    "success",
                    "Quantidades disponíveis",
                    "Todos os equipamentos selecionados podem ser atendidos no período informado.",
                );
                submitButton.disabled = false;
                return;
            }

            const unavailableNames = data.itens
                .filter((item) => !item.disponivel)
                .map((item) => item.nome)
                .join(", ");
            const nextDates = data.proxima_data_retirada
                ? {
                    withdrawal: data.proxima_data_retirada,
                    return: data.proxima_data_devolucao,
                }
                : null;
            const description = nextDates
                ? `${unavailableNames} não atende à quantidade pedida. A próxima janela comum é de ${formatDate(nextDates.withdrawal)} a ${formatDate(nextDates.return)}.`
                : `${unavailableNames} não possui estoque suficiente para a quantidade pedida.`;
            showNotice("error", "Quantidade indisponível neste período", description, nextDates);
            submitButton.disabled = true;
        } catch (error) {
            if (currentSequence !== requestSequence) {
                return;
            }
            showNotice(
                "error",
                "Não foi possível conferir o estoque",
                error.message,
            );
            submitButton.disabled = false;
        }
    };

    const scheduleAvailabilityCheck = () => {
        window.clearTimeout(debounceTimer);
        debounceTimer = window.setTimeout(checkAvailability, 250);
    };

    equipmentOptions.forEach((option) => {
        const checkbox = getCheckbox(option);
        const quantityInput = getQuantityInput(option);

        checkbox.addEventListener("change", () => {
            quantityInput.value = checkbox.checked ? Math.max(clampQuantity(option, quantityInput.value), 1) : 0;
            updateSelectedEquipment();
            scheduleAvailabilityCheck();
        });

        quantityInput.addEventListener("input", () => {
            updateSelectedEquipment();
            scheduleAvailabilityCheck();
        });

        option.querySelectorAll("[data-quantity-action]").forEach((button) => {
            button.addEventListener("click", () => {
                const direction = button.dataset.quantityAction === "increase" ? 1 : -1;
                quantityInput.value = clampQuantity(option, Number(quantityInput.value) + direction);
                updateSelectedEquipment();
                scheduleAvailabilityCheck();
            });
        });
    });

    withdrawalInput.addEventListener("change", scheduleAvailabilityCheck);
    returnInput.addEventListener("change", scheduleAvailabilityCheck);
    suggestedDatesButton.addEventListener("click", () => {
        if (!suggestedDates) {
            return;
        }
        withdrawalInput.value = suggestedDates.withdrawal;
        returnInput.value = suggestedDates.return;
        checkAvailability();
        withdrawalInput.focus();
    });

    updateSelectedEquipment();
    if (getSelectedItems().length > 0) {
        scheduleAvailabilityCheck();
    }
});
