# -*- coding: utf-8 -*-
"""
Valida a planilha gbics.csv antes de publicar.
Sai com codigo 1 (erro) se encontrar problemas; 0 se estiver tudo certo.
Nao depende de bibliotecas externas (so a biblioteca padrao).
"""
import csv
import sys

ARQUIVO = "gbics.csv"
NUMERICAS = ["tx_min", "tx_max", "rx_min", "rx_max", "budget"]
OBRIGATORIAS = ["fabricante", "modelo"] + NUMERICAS


def para_numero(valor):
    # aceita virgula ou ponto como separador decimal
    return float(str(valor).strip().replace(",", "."))


def main():
    try:
        with open(ARQUIVO, encoding="utf-8-sig", newline="") as f:
            leitor = csv.DictReader(f)
            colunas = leitor.fieldnames or []
            faltando = [c for c in OBRIGATORIAS if c not in colunas]
            if faltando:
                print("VALIDACAO FALHOU: colunas ausentes -> " + ", ".join(faltando))
                return 1

            problemas = []
            linha = 1  # a linha 1 e o cabecalho
            total = 0
            for row in leitor:
                linha += 1
                total += 1
                modelo = (row.get("modelo") or "").strip()
                try:
                    tx_min = para_numero(row["tx_min"])
                    tx_max = para_numero(row["tx_max"])
                    rx_min = para_numero(row["rx_min"])
                    rx_max = para_numero(row["rx_max"])
                    budget = para_numero(row["budget"])
                except (ValueError, TypeError, KeyError):
                    problemas.append((linha, modelo, "valor numerico invalido"))
                    continue

                if tx_min > tx_max:
                    problemas.append((linha, modelo,
                                      "TX invertido (tx_min %s > tx_max %s)" % (tx_min, tx_max)))
                if rx_min > rx_max:
                    problemas.append((linha, modelo,
                                      "RX invertido (rx_min %s > rx_max %s)" % (rx_min, rx_max)))
                if budget <= 0:
                    problemas.append((linha, modelo, "budget invalido (%s)" % budget))
    except FileNotFoundError:
        print("VALIDACAO FALHOU: arquivo gbics.csv nao encontrado.")
        return 1

    if problemas:
        print("VALIDACAO FALHOU - %d problema(s):" % len(problemas))
        print("")
        for ln, mod, msg in problemas:
            print("  Linha %d  [%s]: %s" % (ln, mod, msg))
        print("")
        print("Corrija a planilha e tente publicar novamente.")
        return 1

    print("Validacao OK - %d modelos, nenhum problema." % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
