from collections import defaultdict
from datetime import timedelta

from .models import ItemSolicitacao, SolicitacaoEmprestimo


def _reservas_confirmadas(equipamentos_ids, data_inicial, excluir_solicitacao_id=None):
    reservas = ItemSolicitacao.objects.filter(
        equipamento_id__in=equipamentos_ids,
        solicitacao__status=SolicitacaoEmprestimo.Status.CONFIRMADO,
        solicitacao__data_devolucao__gte=data_inicial,
    )
    if excluir_solicitacao_id:
        reservas = reservas.exclude(solicitacao_id=excluir_solicitacao_id)

    return list(
        reservas.values(
            "equipamento_id",
            "quantidade",
            "solicitacao__data_retirada",
            "solicitacao__data_devolucao",
        )
    )


def _avaliar_periodo(itens, data_retirada, data_devolucao, reservas):
    disponibilidades = []

    for equipamento, quantidade in itens:
        eventos = defaultdict(int)
        eventos[data_retirada] = 0

        for reserva in reservas:
            if reserva["equipamento_id"] != equipamento.pk:
                continue

            inicio_reserva = max(
                data_retirada,
                reserva["solicitacao__data_retirada"],
            )
            fim_reserva = min(
                data_devolucao,
                reserva["solicitacao__data_devolucao"],
            )
            if inicio_reserva > fim_reserva:
                continue

            eventos[inicio_reserva] += reserva["quantidade"]
            if fim_reserva < data_devolucao:
                eventos[fim_reserva + timedelta(days=1)] -= reserva["quantidade"]

        quantidade_reservada = 0
        maior_quantidade_reservada = 0
        for data_evento in sorted(eventos):
            quantidade_reservada += eventos[data_evento]
            maior_quantidade_reservada = max(
                maior_quantidade_reservada,
                quantidade_reservada,
            )

        quantidade_disponivel = max(
            equipamento.quantidade_total - maior_quantidade_reservada,
            0,
        )
        disponibilidades.append(
            {
                "equipamento": equipamento,
                "quantidade_solicitada": quantidade,
                "quantidade_disponivel": quantidade_disponivel,
                "disponivel": quantidade <= quantidade_disponivel,
            }
        )

    return disponibilidades


def verificar_disponibilidade(
    itens,
    data_retirada,
    data_devolucao,
    excluir_solicitacao_id=None,
):
    itens = list(itens)
    reservas = _reservas_confirmadas(
        [equipamento.pk for equipamento, _ in itens],
        data_retirada,
        excluir_solicitacao_id,
    )
    disponibilidades = _avaliar_periodo(
        itens,
        data_retirada,
        data_devolucao,
        reservas,
    )
    return {
        "disponivel": all(item["disponivel"] for item in disponibilidades),
        "itens": disponibilidades,
    }


def encontrar_proxima_janela(
    itens,
    data_retirada,
    data_devolucao,
    excluir_solicitacao_id=None,
):
    itens = list(itens)
    if any(
        quantidade > equipamento.quantidade_total
        for equipamento, quantidade in itens
    ):
        return None

    reservas = _reservas_confirmadas(
        [equipamento.pk for equipamento, _ in itens],
        data_retirada,
        excluir_solicitacao_id,
    )
    duracao = data_devolucao - data_retirada
    datas_candidatas = {data_retirada}
    datas_candidatas.update(
        reserva["solicitacao__data_devolucao"] + timedelta(days=1)
        for reserva in reservas
    )

    for proxima_retirada in sorted(datas_candidatas):
        proxima_devolucao = proxima_retirada + duracao
        disponibilidades = _avaliar_periodo(
            itens,
            proxima_retirada,
            proxima_devolucao,
            reservas,
        )
        if all(item["disponivel"] for item in disponibilidades):
            return proxima_retirada, proxima_devolucao

    return None
