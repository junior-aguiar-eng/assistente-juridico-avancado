"""Gera exemplos artificiais do contrato; não extrai nem classifica documentos reais."""
import copy
import hashlib
import json
from pathlib import Path


def sha(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def exemplo(cid, textos, atribuicoes, tipos, *, recortes=None, secoes=None, parcial=False):
    origem = f"Origem artificial {cid}; sem documento de cliente."
    total = max(pf for _, _, pf, _ in textos)
    blocos = [{"id": f"b{i:04d}", "text": texto, "page": pi, "page_end": pf,
               "locator": f"p.{pi}" if pi == pf else f"p.{pi}-{pf}", "section": sec,
               "is_quote": False, "tags": ["ocr"] if parcial else []}
              for i, (texto, pi, pf, sec) in enumerate(textos, 1)]
    ext = {"document_id": "doc-" + sha(origem)[:12], "sha256": sha(origem), "page_count": total,
           "status": "partial" if parcial else "ok", "blocks": blocos,
           "extractor_versions": {"extractor": "1", "nome": "simulado"},
           "warnings": [{"codigo": "ocr_baixa_confianca"}] if parcial else []}
    config = {"simulado": True}
    ext_json = json.dumps({"schema_version": "1", "run": {"params": config}, "documents": [ext]},
                          ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if recortes is None:
        recortes = [(i, 0, len(b["text"])) for i, b in enumerate(blocos)]
    fs = []
    for n, ((bi, inicio, fim), alvo) in enumerate(zip(recortes, atribuicoes), 1):
        b = blocos[bi]
        destino = {"classe": "peca", "piece_id": alvo} if alvo else {
            "classe": "nao_atribuido" if parcial else "auxiliar",
            "motivo": "OCR insuficiente" if parcial else "Rodapé repetido, separado do corpo"}
        fs.append({"id": f"f{n:03d}", "block_id": b["id"], "inicio": inicio, "fim": fim,
                   "paginas": {"inicio": b["page"], "fim": b["page_end"],
                               "precisao": "pagina" if b["page"] == b["page_end"] else "intervalo",
                               "origem": "extracao"}, "destino": destino})
    proposta = {"estado": "proposto", "evento_id": None}
    pecas = []
    for ordem, (pid, tipo) in enumerate(tipos.items(), 1):
        ligados = [f["id"] for f in fs if f["destino"].get("piece_id") == pid]
        pecas.append({"id": pid, "ordem": ordem, "tipo_proposto": tipo,
                      "inicio": ligados[0], "fim": ligados[-1], "proposta_evento_id": "ev-1",
                      "limites": copy.deepcopy(proposta), "tipo": copy.deepcopy(proposta),
                      "evidencias": [{"sinal": "outro", "fragmentos": ligados,
                                      "observacao": "Gabarito artificial do contrato; não é predição nem conferência humana"}]})
    ss = [{"id": f"sec-{i}", "piece_id": pid, "tipo_proposto": tipo, "fragmentos": ids,
           "conferencia": copy.deepcopy(proposta)} for i, (pid, tipo, ids) in enumerate(secoes or [], 1)]
    paginas = [{"numero": n, "leitura": "ocr_parcial" if parcial else "texto_nativo", "origem": "extracao"}
               for n in range(1, total + 1)]
    pendencias = []
    if parcial:
        pendencias = [{"id": "pend-1", "codigo": "leitura_insuficiente", "referencias": ["f001"],
                       "mensagem": "Exemplo artificial: não utilizar o OCR como leitura conferida", "material": True},
                      {"id": "pend-2", "codigo": "fragmento_nao_atribuido", "referencias": ["f001"],
                       "mensagem": "Natureza da peça não identificada", "material": True}]
    inv = {"schema_version": "1", "inventario_id": "inv-" + cid, "revisao": 1, "anterior_sha256": None,
           "origem": {"document_id": ext["document_id"], "arquivo_sha256": sha(origem),
                      "extracao_sha256": sha(ext_json), "total_paginas": total,
                      "extrator": {"nome": "simulado", "versao": "1"},
                      "configuracao_sha256": sha(json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")))},
           "metodo": {"nome": "exemplo_de_contrato", "versao": "1"}, "paginas": paginas,
           "fragmentos": fs, "pecas": pecas, "secoes": ss,
           "eventos": [{"id": "ev-1", "instante": "2026-10-22T00:00:00Z",
                        "ator": {"tipo": "sistema", "identificador": "gerador-de-fixtures-sinteticas"},
                        "acao": "propor", "alvos": list(tipos) or ["inv-" + cid],
                        "motivo": "Simulação de contrato; data e identidades artificiais, sem valor de aprovação"}],
           "pendencias": pendencias}
    return {"id": cid, "natureza": "simulacao_de_contrato", "origem_simulada_utf8": origem,
            "extracao_json_utf8": ext_json, "inventario": inv}


def revisao_fusao():
    anterior = exemplo("RH01", [("PETIÇÃO UM.", 1, 1, "corpo"), ("CONTINUAÇÃO.", 2, 2, "corpo")],
                       ["p001", "p002"], {"p001": "peticao", "p002": "peticao"})["inventario"]
    for n, dimensao in enumerate(("limites", "tipo"), 2):
        anterior["eventos"].append({
            "id": f"ev-{n}", "instante": f"2026-10-22T00:0{n}:00Z",
            "ator": {"tipo": "humano", "identificador": "Pessoa simulada (fixture)"},
            "acao": "conferir_" + dimensao, "alvos": ["p001"],
            "motivo": "Conferência fictícia para testar invalidação; sem aprovação humana real"})
        anterior["pecas"][0][dimensao] = {"estado": "conferido", "evento_id": f"ev-{n}"}
    anterior_json = json.dumps(anterior, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    atual = copy.deepcopy(anterior)
    atual["revisao"] = 2
    atual["anterior_sha256"] = sha(anterior_json)
    atual["pecas"].pop()
    atual["fragmentos"][1]["destino"]["piece_id"] = "p001"
    peca = atual["pecas"][0]
    peca["fim"] = "f002"
    peca["proposta_evento_id"] = "ev-4"
    peca["evidencias"][0]["fragmentos"] = ["f001", "f002"]
    for dimensao in ("limites", "tipo"):
        peca[dimensao] = {"estado": "proposto", "evento_id": None}
    atual["eventos"].append({
        "id": "ev-4", "instante": "2026-10-22T00:04:00Z",
        "ator": {"tipo": "sistema", "identificador": "gerador-de-fixtures-sinteticas"},
        "acao": "corrigir", "alvos": ["p001", "p002"],
        "motivo": "Fusão artificial: remove p002, amplia p001 e invalida conferências apoiadas no conteúdo anterior"})
    return {"id": "RH01", "natureza": "simulacao_de_contrato",
            "anterior_json_utf8": anterior_json, "inventario": atual}


def gerar():
    multi = exemplo("CT06", [("Fim da sentença. Início do acórdão.", 1, 2, "sentenca")],
                    ["p001", "p002"], {"p001": "sentenca", "p002": "acordao"},
                    recortes=[(0, 0, 17), (0, 17, 35)])
    for pagina, fragmento in enumerate(multi["inventario"]["fragmentos"], 1):
        fragmento["paginas"] = {"inicio": pagina, "fim": pagina, "precisao": "pagina", "origem": "conferencia_visual"}
    vazio = exemplo("CT07", [("CAPA E ÍNDICE.", 1, 1, "cabecalho"),
                             ("Continuação sem título identificável.", 3, 3, "corpo")],
                    [None, "p001"], {"p001": "nao_identificada"})
    vazio["inventario"]["fragmentos"][0]["destino"]["motivo"] = "Capa/índice, sem natureza de peça atribuída"
    vazio["inventario"]["paginas"][1]["leitura"] = "sem_texto"
    vazio["inventario"]["pendencias"] = [
        {"id": "pend-1", "codigo": "pagina_sem_texto", "referencias": ["pagina-2"], "mensagem": "Folha vazia no exemplo artificial", "material": True},
        {"id": "pend-2", "codigo": "tipo_nao_identificado", "referencias": ["p001"], "mensagem": "Tipo não conferido", "material": True}]
    ext = json.loads(vazio["extracao_json_utf8"])
    ext["documents"][0]["warnings"].append({"codigo": "pagina_sem_texto", "pagina": 2})
    vazio["extracao_json_utf8"] = json.dumps(ext, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    vazio["inventario"]["origem"]["extracao_sha256"] = sha(vazio["extracao_json_utf8"])
    return {"descricao": "Simulações anônimas de contrato; não são PDFs extraídos nem resultados de segmentação.",
            "exemplos": [
        exemplo("CT01", [("SENTENÇA. Julgo o pedido.", 1, 1, "sentenca"),
                         ("A C Ó R D Ã O", 2, 2, "sentenca"), ("RELATÓRIO. Síntese.", 2, 2, "sentenca"),
                         ("VOTO. Fundamentos.", 2, 2, "sentenca")],
                ["p001", "p002", "p002", "p002"], {"p001": "sentenca", "p002": "acordao"},
                secoes=[("p002", "relatorio", ["f003"]), ("p002", "voto", ["f004"])]),
        exemplo("CT02", [("PETIÇÃO A. PETIÇÃO B.", 1, 1, "corpo")], ["p001", "p002"],
                {"p001": "peticao", "p002": "peticao"}, recortes=[(0, 0, 11), (0, 11, 21)]),
        exemplo("CT03", [("PETIÇÃO UM.", 1, 1, "corpo"), ("PETIÇÃO DOIS.", 2, 2, "corpo")],
                ["p001", "p002"], {"p001": "peticao", "p002": "peticao"}),
        exemplo("CT04", [("Acórdão cita a palavra SENTENÇA de outro julgado.", 1, 1, "corpo"),
                         ("VOTO. A citação não abre outra peça.", 2, 2, "corpo"),
                         ("Rodapé repetido", 1, 2, "rodape")], ["p001", "p001", None], {"p001": "acordao"},
                secoes=[("p001", "voto", ["f002"])]),
        exemplo("CT05", [("Texto OCR incerto: [ilegível].", 1, 1, "cabecalho")], [None], {}, parcial=True),
        multi, vazio
    ], "revisoes": [revisao_fusao()]}


if __name__ == "__main__":
    Path(__file__).with_name("exemplos.json").write_text(json.dumps(gerar(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
