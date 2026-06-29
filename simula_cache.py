import sys
import random
from math import log2


def potencia_de_2(n):
    return n > 0 and (n & (n - 1)) == 0


def carregar_enderecos(caminho):
    enderecos = []
    with open(caminho) as f:
        for linha in f:
            partes = linha.split()
            if len(partes) >= 2:
                enderecos.append((int(partes[0], 16), partes[1].upper()))
    return enderecos


def escolher_vitima(conjunto, substituicao):
    for i, linha in enumerate(conjunto):
        if linha is None:
            return i, False
    if substituicao == "LRU":
        i = min(range(len(conjunto)), key=lambda k: conjunto[k]["uso"])
    else:
        i = random.randrange(len(conjunto))
    return i, True


def instalar(conjunto, rotulo, relogio, substituicao, sujo):
    i, substituiu = escolher_vitima(conjunto, substituicao)
    vitima_suja = substituiu and conjunto[i]["dirty"] == 1
    conjunto[i] = {"rotulo": rotulo, "dirty": 1 if sujo else 0, "uso": relogio}
    return vitima_suja


def main():
    if len(sys.argv) != 9:
        print("uso: simula_cache <pol_escrita> <tam_linha> <num_linhas> "
              "<assoc> <hit_time> <substituicao> <tempo_mem> <arquivo>")
        return

    pol_escrita = int(sys.argv[1])       # 0 write-through, 1 write-back
    tam_linha = int(sys.argv[2])         # bytes
    num_linhas = int(sys.argv[3])
    assoc = int(sys.argv[4])
    hit_time = float(sys.argv[5])        # ns
    substituicao = sys.argv[6].upper()
    tempo_mem = float(sys.argv[7])       # ns (leitura/escrita)
    arquivo = sys.argv[8]

    if pol_escrita not in (0, 1):
        print("politica de escrita invalida (use 0 ou 1)")
        return
    for nome, valor in (("tam_linha", tam_linha),
                        ("num_linhas", num_linhas),
                        ("assoc", assoc)):
        if not potencia_de_2(valor):
            print(f"{nome} deve ser potencia de 2")
            return
    if assoc > num_linhas:
        print("associatividade nao pode exceder o numero de linhas")
        return
    if substituicao not in ("LRU", "ALEATORIA", "ALEATÓRIA", "RANDOM"):
        print("substituicao deve ser LRU ou ALEATORIA")
        return
    if substituicao != "LRU":
        substituicao = "ALEATORIA"

    write_back = pol_escrita == 1
    num_conjuntos = num_linhas // assoc
    bits_offset = int(log2(tam_linha))

    cache = [[None] * assoc for _ in range(num_conjuntos)]

    leituras = escritas = 0
    acertos_leitura = acertos_escrita = 0
    mp_leituras = mp_escritas = 0
    relogio = 0

    for endereco, operacao in carregar_enderecos(arquivo):
        relogio += 1
        bloco = endereco >> bits_offset
        indice = bloco % num_conjuntos
        rotulo = bloco // num_conjuntos
        conjunto = cache[indice]

        pos = -1
        for i, linha in enumerate(conjunto):
            if linha is not None and linha["rotulo"] == rotulo:
                pos = i
                break
        acerto = pos != -1

        if operacao == "R":
            leituras += 1
            if acerto:
                acertos_leitura += 1
                conjunto[pos]["uso"] = relogio
            else:
                mp_leituras += 1
                if instalar(conjunto, rotulo, relogio, substituicao, False):
                    mp_escritas += 1
        else:
            escritas += 1
            if write_back:
                if acerto:
                    acertos_escrita += 1
                    conjunto[pos]["dirty"] = 1
                    conjunto[pos]["uso"] = relogio
                else:
                    mp_leituras += 1
                    if instalar(conjunto, rotulo, relogio, substituicao, True):
                        mp_escritas += 1
            else:
                mp_escritas += 1
                if acerto:
                    acertos_escrita += 1
                    conjunto[pos]["uso"] = relogio

    # atualiza a memoria principal com as linhas sujas restantes (write-back)
    if write_back:
        for conjunto in cache:
            for linha in conjunto:
                if linha is not None and linha["dirty"] == 1:
                    mp_escritas += 1

    total = leituras + escritas
    acertos = acertos_leitura + acertos_escrita
    tx_leitura = acertos_leitura / leituras if leituras else 0.0
    tx_escrita = acertos_escrita / escritas if escritas else 0.0
    tx_global = acertos / total if total else 0.0
    tempo_medio = hit_time + (1.0 - tx_global) * tempo_mem

    print("--- Parametros ---")
    print(f"Politica de escrita: {'write-back' if write_back else 'write-through'}")
    print(f"Tamanho da linha (bytes): {tam_linha}")
    print(f"Numero de linhas: {num_linhas}")
    print(f"Associatividade: {assoc}")
    print(f"Numero de conjuntos: {num_conjuntos}")
    print(f"Hit time (ns): {hit_time:.4f}")
    print(f"Politica de substituicao: {substituicao}")
    print(f"Tempo de leitura/escrita da MP (ns): {tempo_mem:.4f}")

    print("\n--- Enderecos ---")
    print(f"Leituras: {leituras}")
    print(f"Escritas: {escritas}")
    print(f"Total: {total}")

    print("\n--- Acessos a memoria principal ---")
    print(f"Leituras na MP: {mp_leituras}")
    print(f"Escritas na MP: {mp_escritas}")

    print("\n--- Taxa de acerto ---")
    print(f"Leitura: {tx_leitura * 100:.4f}% ({acertos_leitura} de {leituras})")
    print(f"Escrita: {tx_escrita * 100:.4f}% ({acertos_escrita} de {escritas})")
    print(f"Global:  {tx_global * 100:.4f}% ({acertos} de {total})")

    print(f"\nTempo medio de acesso (ns): {tempo_medio:.4f}")


if __name__ == "__main__":
    main()
