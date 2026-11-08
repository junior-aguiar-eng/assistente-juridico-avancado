"""Gate final de uma entrega: checagem técnica (qc.json) e aprovação humana ligada a hashes.

  auditar  --facts F.json --claims C.json --extracoes E.json [--modo fundamentada|analise]
           [--timeline T.json] [--matter M.json] [--tipo-entrega interna|cliente|peticao|contrato]
           [--issues I.json] [--campos C.json --modelo M.docx --minuta D.docx]
           [--regras DIR --pacote servicos_saas,lgpd]
           [--reverificar N] [--relatorio R.md ...] [--artefato ARQ ...] --saida qc.json
  aprovar  qc.json --revisor NOME [--registro OAB/UF] --declaracao TEXTO [--decisao aprovada|reprovada]
           [--nota TEXTO] --saida aprovacao.json
  status   qc.json [aprovacao.json]

`aprovar` só funciona em terminal interativo e exige que o revisor digite a frase de confirmação.
A checagem técnica diz "revisao_pronta" ou "bloqueado". Nunca é aprovação: "aprovada" só
existe em aprovacao.json, registrada por pessoa identificada, e vale enquanto nenhum
artefato (incluindo as fontes lidas) mudar. Quem decide a correção jurídica é o revisor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate  # noqa: E402

SCHEMA_VERSION = "1"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(p: Path, base: Path) -> str:
    try:
        return Path(os.path.relpath(p, base)).as_posix()
    except ValueError:  # outra unidade no Windows
        return p.resolve().as_posix()


def _resolver(caminho: str, *bases: Path) -> Path | None:
    p = Path(caminho)
    for cand in ([p] if p.is_absolute() else [b / p for b in bases] + [Path.cwd() / p]):
        if cand.is_file():
            return cand
    return None


class Gates:
    def __init__(self):
        self.itens: list[dict] = []
        self.pendencias: list[dict] = []

    def add(self, gid, descricao, resultado, detalhe=""):
        self.itens.append({"id": gid, "descricao": descricao, "resultado": resultado, "detalhe": detalhe})

    def pend(self, origem, item, motivo):
        self.pendencias.append({"origem": origem, "item": item, "motivo": motivo})


def _resumo_erros(r, n=8):
    return "; ".join(f"{e['codigo']} em {e['caminho']}" for e in r.erros[:n]) + (" ..." if len(r.erros) > n else "")


TIPOS_ENTREGA = ("interna", "cliente", "peticao", "contrato")
MARCA_AVISO = "não constitui parecer"


def _baixar(url, destino):
    import fontes

    return fontes.baixar(url, destino)


def auditar(facts, claims, extracoes, modo="fundamentada", extras=(), base=Path("."), timeline=None,
            matter=None, tipo_entrega="interna", reverificar=0, relatorios=(), sem_teses_centrais=False,
            issues=None, campos=None, modelo=None, minuta=None, regras_dir=None, pacote="servicos_saas,lgpd", *,
            pecas=(), pecas_anteriores=(), exigir_pecas=False) -> dict:
    g = Gates()
    externa = tipo_entrega != "interna"
    rigor = "reprovado" if (modo == "fundamentada" or externa) else "alerta"
    base = Path(base).resolve()
    idx, docs, dirs_ext = {}, [], []
    for e in extracoes:
        ep = Path(e).resolve()
        dirs_ext.append(ep.parent)
        for d in validate.carregar_extracoes([ep]).values():
            idx[d["document_id"]] = d
        obj = json.loads(ep.read_text(encoding="utf-8"))
        docs += obj.get("documents", [obj] if "blocks" in obj else [])
    artefatos = {}
    import pecas_uso
    contexto = pecas_uso.carregar_contexto(extracoes, pecas, anteriores=pecas_anteriores, exigir=exigir_pecas)
    erros_pecas, avisos_pecas = list(contexto.erros), []

    def reg(caminho, tipo):
        p = Path(caminho).resolve()
        artefatos[p] = tipo

    for caminho, tipo in contexto.artefatos:
        reg(caminho, tipo)

    # G00: sem extração nada é conferido contra o texto lido (trechos, localizadores, hashes)
    if extracoes:
        g.add("G00_extracao_presente", "trechos e hashes conferidos contra o texto extraído", "aprovado",
              f"{len(docs)} documento(s) extraído(s)")
    else:
        g.add("G00_extracao_presente", "trechos e hashes conferidos contra o texto extraído",
              rigor,
              "sem extração informada: nenhum trecho, localizador ou hash foi conferido contra o texto lido")

    objs, avisos_val = {}, []
    for rot, cam, fn in (("facts", facts, validate.validar_facts), ("claims", claims, validate.validar_claims)):
        gid = "G01_schema_facts" if rot == "facts" else "G02_schema_claims"
        if not cam:
            g.add(gid, f"{rot}.json válido contra as regras e as fontes extraídas", "nao_aplicavel", "arquivo não informado")
            continue
        try:
            objs[rot] = json.loads(Path(cam).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            g.add(gid, f"{rot}.json válido", "reprovado", f"ilegível: {e}")
            continue
        r = fn(objs[rot], idx if extracoes else None, pecas=contexto if contexto.ativo else None,
               modo="fundamentada" if rigor == "reprovado" else "analise")
        erros_pecas += [e for e in r.erros if e['codigo'].startswith('pecas_')]
        avisos_pecas += [a for a in r.avisos if a['codigo'].startswith('pecas_')]
        avisos_val += [(rot, a) for a in r.avisos]
        g.add(gid, f"{rot}.json válido contra as regras e as fontes extraídas",
              "reprovado" if r.erros else "aprovado", _resumo_erros(r) if r.erros else f"{len(r.avisos)} aviso(s)")
        reg(cam, rot)
    for e in extracoes:
        reg(e, "extracao")
    for x in extras:
        reg(x, "artefato")

    # G03 cobertura de leitura
    lacunas = [f for f in objs.get("facts", {}).get("facts", []) if isinstance(f, dict) and f.get("kind") == "lacuna"]
    nao_ok = [d for d in docs if d.get("status") != "ok"]
    sem_lacuna, so_pelo_nome = [], []
    for d in nao_ok:
        nome = Path(d.get("path", "")).name
        forte = any(f.get("document_id") and f.get("document_id") == d.get("document_id") for f in lacunas)
        fraco = any(nome and nome in f.get("text", "") for f in lacunas)
        g.pend("cobertura", nome or "(sem nome)", f"documento {d.get('status')}: {[a['codigo'] for a in d.get('warnings', [])]}")
        if not forte and fraco:
            so_pelo_nome.append(nome)
        elif not forte:
            sem_lacuna.append(d)
    if not docs:
        g.add("G03_cobertura_leitura", "todo documento lido ou registrado como lacuna", "alerta", "nenhuma extração informada")
    elif not nao_ok:
        g.add("G03_cobertura_leitura", "todo documento lido ou registrado como lacuna", "aprovado", f"{len(docs)} documento(s) com status ok")
    elif "facts" not in objs:
        g.add("G03_cobertura_leitura", "todo documento lido ou registrado como lacuna", "alerta",
              f"{len(nao_ok)} documento(s) não lido(s) por inteiro e sem facts.json para registrar as lacunas")
    elif sem_lacuna:
        g.add("G03_cobertura_leitura", "todo documento lido ou registrado como lacuna", "reprovado",
              "falha silenciosa: sem lacuna registrada para " + ", ".join(Path(d["path"]).name for d in sem_lacuna))
    elif so_pelo_nome:
        g.add("G03_cobertura_leitura", "todo documento lido ou registrado como lacuna", "alerta",
              "lacuna ligada ao documento só pelo nome do arquivo no texto livre: acrescente 'document_id' à lacuna ("
              + ", ".join(so_pelo_nome) + ")")
    else:
        g.add("G03_cobertura_leitura", "todo documento lido ou registrado como lacuna", "aprovado",
              f"{len(nao_ok)} documento(s) não lido(s) por inteiro, todos registrados como lacuna (por document_id)")

    # G04 originais intactos desde a extração
    mudou, ausente = [], []
    for d in docs:
        if not d.get("sha256"):
            continue
        p = _resolver(d["path"], *dirs_ext)
        if p is None and d.get("document_id") in contexto.documentos:
            p = contexto.documentos[d["document_id"]]["original"]
        if p is None:
            ausente.append(d["path"])
        else:
            reg(p, "fonte")
            if _sha(p) != d["sha256"]:
                mudou.append(d["path"])
    g.add("G04_originais_intactos", "arquivos de origem iguais aos extraídos",
          "reprovado" if mudou else (rigor if ausente else "aprovado"),
          ("alterados após a extração: " + ", ".join(mudou)) if mudou else
          (("não localizados para conferir: " + ", ".join(ausente)) if ausente else f"{len(docs)} arquivo(s) conferido(s)"))

    # G05 fontes lidas dos claims conferem com os arquivos
    div, falt, conf, sem_local = [], [], 0, []
    if "claims" in objs:
        pasta = Path(claims).resolve().parent
        for c in objs["claims"].get("claims", []):
            fontes_c = [s for s in c.get("sources", []) if isinstance(s, dict)] if isinstance(c, dict) else []
            oficiais = [s for s in fontes_c if s.get("access") == "lida" and s.get("origin") == "oficial"]
            if c.get("status") == "supported" and oficiais and not any(s.get("local_file") for s in oficiais):
                sem_local.append(str(c.get("id")))
                g.pend("fonte_nao_reconferivel", c.get("id"), "proposição 'supported' sem local_file: a leitura não pode ser refeita")
            for s in fontes_c:
                if s.get("access") != "lida" or not s.get("local_file"):
                    continue
                p = _resolver(s["local_file"], pasta, *dirs_ext)
                if p is None:
                    falt.append(s["local_file"])
                    continue
                reg(p, "fonte")
                did = s.get("document_id")
                extraido = idx.get(did, {}) if isinstance(did, str) else {}
                # Hash textual identifica o texto registrado; a integridade do arquivo
                # local exige os bytes do documento do qual esse texto foi extraído.
                bruto = extraido.get("sha256") if extraido else s.get("content_hash")
                aceitos = {h for h in (bruto, extraido.get("text_sha256")) if h}
                if _sha(p) == bruto and s.get("content_hash") in aceitos:
                    conf += 1
                else:
                    div.append(f"{c.get('id')}:{s['local_file']}")
        detalhes = []
        if div:
            detalhes.append("hash diverge em " + ", ".join(div))
        if falt:
            detalhes.append("arquivo ausente: " + ", ".join(falt))
        if sem_local:
            detalhes.append("sem local_file (não reconferível): " + ", ".join(sem_local))
        g.add("G05_fontes_lidas_conferem", "arquivo de cada fonte lida confere com o hash registrado",
              "reprovado" if div else (rigor if (falt or sem_local) else "aprovado"),
              "; ".join(detalhes) or f"{conf} fonte(s) conferida(s)")
    else:
        g.add("G05_fontes_lidas_conferem", "arquivo de cada fonte lida confere com o hash registrado", "nao_aplicavel", "sem claims.json")

    # G06 teses centrais e G07 proposições refutadas
    cl = [c for c in objs.get("claims", {}).get("claims", []) if isinstance(c, dict)]
    if "claims" in objs:
        centrais = [c for c in cl if c.get("central") is True]
        pend = [c for c in centrais if c.get("status") != "supported"]
        for c in pend:
            g.pend("tese_central", c.get("id"), f"estado {c.get('status')}")
        if not centrais:
            if sem_teses_centrais:
                g.add("G06_teses_centrais", "teses centrais com apoio verificado", "alerta",
                      "declarado pelo usuário: nenhuma proposição é tese central (--sem-teses-centrais)")
            else:
                g.add("G06_teses_centrais", "teses centrais com apoio verificado", rigor,
                      "nenhuma proposição marcada como central: marque as que sustentam a peça ou declare --sem-teses-centrais")
        elif pend:
            g.add("G06_teses_centrais", "teses centrais com apoio verificado",
                  rigor,
                  f"{len(pend)} de {len(centrais)} sem 'supported': " + ", ".join(str(c.get("id")) for c in pend))
        else:
            g.add("G06_teses_centrais", "teses centrais com apoio verificado", "aprovado", f"{len(centrais)} central(is) 'supported'")
        for c in cl:
            if c.get("status") in ("unverified", "partial", "unsupported") and c not in pend:
                g.pend("proposicao", c.get("id"), f"estado {c.get('status')}")
        ref = [c for c in cl if c.get("status") == "unsupported"]
        contraditas = [c for c in ref if c.get("source_relation") == "contradiz"]
        por_id = {c.get("id"): c for c in cl}
        dependentes = []  # argumentos que dependem de proposição sem apoio pleno
        for c in cl:
            for d in c.get("depends_on") or []:
                alvo = por_id.get(d)
                if alvo is not None and alvo.get("status") != "supported":
                    dependentes.append(f"{c.get('id')} depende de {d} ({alvo.get('status')})")
                    g.pend("dependencia", c.get("id"), f"depende de {d}, que está '{alvo.get('status')}'")
        for c in contraditas:
            g.pend("escalar", c.get("id"), "a fonte oficial lida contradiz a proposição: levar ao advogado antes de seguir"
                   + (" (tese central)" if c.get("central") is True else ""))
        detalhes = []
        if ref:
            detalhes.append("confirme que não entram como fundamento: " + ", ".join(str(c.get("id")) for c in ref))
        if contraditas:
            detalhes.append("contraditas pela fonte (escalar): " + ", ".join(str(c.get("id")) for c in contraditas))
        if dependentes:
            detalhes.append("dependências em risco: " + "; ".join(dependentes))
        g.add("G07_proposicoes_refutadas", "proposição refutada pela fonte não consta como fundamento",
              "alerta" if (ref or dependentes) else "aprovado", " | ".join(detalhes) or "nenhuma refutada")
    else:
        g.add("G06_teses_centrais", "teses centrais com apoio verificado", "nao_aplicavel", "sem claims.json")
        g.add("G07_proposicoes_refutadas", "proposição refutada pela fonte não consta como fundamento", "nao_aplicavel", "sem claims.json")
    for f in lacunas:
        g.pend("lacuna", f.get("id"), f.get("text", "")[:140])

    # G08 avisos do validador
    por_cod: dict[str, int] = {}
    for rot, a in avisos_val:
        por_cod[a["codigo"]] = por_cod.get(a["codigo"], 0) + 1
        g.pend("aviso", f"{rot}:{a['caminho']}", a["codigo"])
    g.add("G08_avisos_do_validador", "avisos do validador examinados pelo revisor",
          "alerta" if por_cod else "aprovado", ", ".join(f"{k} x{v}" for k, v in sorted(por_cod.items())) or "nenhum aviso")

    # G09 cronologia atualizada em relação ao facts.json
    if timeline:
        reg(timeline, "timeline")
        if not facts:
            g.add("G09_cronologia_atualizada", "cronologia corresponde ao facts.json", "reprovado", "cronologia sem facts.json")
        else:
            import cronologia

            try:
                c = cronologia.conferir(facts, timeline, pecas_contexto=contexto if contexto.ativo else None)
                g.add("G09_cronologia_atualizada", "cronologia corresponde ao facts.json",
                      "aprovado" if c["atualizada"] else "reprovado",
                      "atualizada" if c["atualizada"] else "desatualizada: gere a cronologia de novo a partir do facts.json atual")
            except (OSError, ValueError, KeyError) as e:
                g.add("G09_cronologia_atualizada", "cronologia corresponde ao facts.json", "reprovado", f"ilegível: {e}")

    # G10 aviso padrão nos relatórios de entrega
    if relatorios:
        sem_aviso = []
        for rel in relatorios:
            reg(rel, "relatorio")
            try:
                if MARCA_AVISO not in Path(rel).read_text(encoding="utf-8").lower():
                    sem_aviso.append(Path(rel).name)
            except OSError:
                sem_aviso.append(f"{Path(rel).name} (ilegível)")
        g.add("G10_aviso_no_relatorio", "relatórios de entrega trazem o aviso padrão (shared/aviso-padrao.md)",
              rigor if sem_aviso else "aprovado", ("sem o aviso: " + ", ".join(sem_aviso)) if sem_aviso else f"{len(relatorios)} relatório(s) com aviso")
    else:
        g.add("G10_aviso_no_relatorio", "relatórios de entrega trazem o aviso padrão (shared/aviso-padrao.md)",
              "reprovado" if externa else "nao_aplicavel",
              "entrega externa exige relatório (--relatorio)" if externa else "nenhum relatório informado (--relatorio)")

    # G11 conflito de interesses e G12 sigilo, a partir do matter.json
    mj = None
    if matter:
        reg(matter, "matter")
        try:
            mj = json.loads(Path(matter).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            g.add("G11_conflitos_de_interesse", "resultado da checagem de conflito registrado", "reprovado", f"matter.json ilegível: {e}")
        else:
            rm = validate.validar_matter(mj, idx if extracoes else None)
            if rm.erros:
                g.add("G11_conflitos_de_interesse", "resultado da checagem de conflito registrado", "reprovado",
                      "matter.json inválido: " + _resumo_erros(rm))
                mj = None
    if mj is not None:
        m = mj["matter"]
        cf = m.get("conflicts") or {}
        st = cf.get("status")
        if st in ("cleared", "waived", "nao_aplicavel"):
            g.add("G11_conflitos_de_interesse", "resultado da checagem de conflito registrado", "aprovado", f"status {st}")
        elif st == "not-run" and cf.get("override"):
            g.add("G11_conflitos_de_interesse", "resultado da checagem de conflito registrado", "alerta",
                  "checagem dispensada por bypass registrado: " + str(cf["override"].get("rationale")))
            g.pend("conflitos", "matter", "bypass registrado: revisar quando a checagem for feita")
        else:
            g.add("G11_conflitos_de_interesse", "resultado da checagem de conflito registrado", rigor,
                  f"status {st or 'não registrado'}: faça a checagem (o pacote só registra o resultado)")
            g.pend("conflitos", "matter", f"conflito de interesses {st or 'não registrado'}")
        conf = m.get("confidentiality") or {}
        posture, sj = conf.get("privilegio"), conf.get("segredo_de_justica")
        fatos = [f for f in objs.get("facts", {}).get("facts", []) if isinstance(f, dict)]
        nao_ok = [f.get("id") for f in fatos if f.get("priv") != "ok"]
        if posture == "nao_triado":
            g.add("G12_sigilo_das_fontes", "fontes triadas quanto a sigilo antes de circular", rigor,
                  "as fontes não foram triadas: triar antes de qualquer entrega")
            g.pend("sigilo", "matter", "fontes sem triagem de sigilo profissional")
        elif posture == "misto" and nao_ok:
            g.add("G12_sigilo_das_fontes", "fontes triadas quanto a sigilo antes de circular", "alerta",
                  f"triagem mista: {len(nao_ok)} fato(s) sem 'priv: ok' (sinalizados para revisão)")
            g.pend("sigilo", "facts", f"{len(nao_ok)} fato(s) sinalizados ou sem marca de sigilo: " + ", ".join(map(str, nao_ok[:8])))
        elif sj is True:
            g.add("G12_sigilo_das_fontes", "fontes triadas quanto a sigilo antes de circular", "alerta", "processo em segredo de justiça")
            g.pend("sigilo", "matter", "segredo de justiça: confirmar que a circulação é permitida (CPC, art. 189)")
        else:
            g.add("G12_sigilo_das_fontes", "fontes triadas quanto a sigilo antes de circular", "aprovado", f"privilégio: {posture or 'não registrado'}")
    elif not matter:
        detalhe = "matter.json não informado"
        g.add("G11_conflitos_de_interesse", "resultado da checagem de conflito registrado", rigor if externa else "nao_aplicavel",
              detalhe + (": entrega externa exige o registro" if externa else ""))
        g.add("G12_sigilo_das_fontes", "fontes triadas quanto a sigilo antes de circular", rigor if externa else "nao_aplicavel", detalhe)

    # G13 reverificação das fontes (reler a fonte oficial e comparar o texto com o lido)
    if reverificar:
        import tempfile

        import extract as _extract

        cand = []
        for c in cl:
            for s in c.get("sources", []) if isinstance(c, dict) else []:
                if (c.get("status") == "supported" and s.get("access") == "lida" and s.get("origin") == "oficial"
                        and s.get("url") and isinstance(s.get("document_id"), str) and s["document_id"] in idx):
                    cand.append((0 if c.get("central") is True else 1, str(c.get("id")), s))
        cand.sort(key=lambda x: (x[0], x[1]))
        mudou, falhou, iguais = [], [], 0
        for _, cid, s in cand[:reverificar]:
            with tempfile.TemporaryDirectory() as tmp:
                r = _baixar(s["url"], Path(tmp))
                if r.get("status") != "lida":
                    falhou.append(f"{cid} ({r.get('motivo', 'sem resposta')})")
                    continue
                novo, _ = _extract.extrair(r["local_file"])
            if novo.get("text_sha256") == idx[s["document_id"]].get("text_sha256"):
                iguais += 1
            else:
                mudou.append(cid)
                g.pend("fonte_mudou", cid, "a fonte oficial relida tem texto diferente do lido: reler antes de entregar")
        if not cand:
            g.add("G13_reverificacao", "fontes oficiais relidas e iguais às registradas", "alerta",
                  "nenhuma fonte elegível (supported, oficial, com url e extração)")
        else:
            partes = [f"{iguais} igual(is)"]
            if mudou:
                partes.append("texto mudou em " + ", ".join(mudou))
            if falhou:
                partes.append("não foi possível reler: " + ", ".join(falhou))
            g.add("G13_reverificacao", "fontes oficiais relidas e iguais às registradas",
                  rigor if mudou else ("alerta" if falhou else "aprovado"), "; ".join(partes))

    import auditoria_documental

    issues, campos = auditoria_documental.identificar(issues, campos, extras)
    documentos = auditoria_documental.conferir(g, reg, idx, bool(extracoes), issues, campos, modelo, minuta, regras_dir, pacote)
    if contexto.ativo or erros_pecas or avisos_pecas:
        for item in erros_pecas + avisos_pecas:
            g.pend("pecas", item['caminho'], item['codigo'])
        g.add("G16_inventario_pecas", "inventários íntegros e referências aptas para o uso declarado",
              "reprovado" if erros_pecas else ("alerta" if avisos_pecas else "aprovado"),
              "; ".join(sorted({i['codigo'] for i in erros_pecas + avisos_pecas})) or "referências conferidas; não é aprovação jurídica")
    reprovados = [i for i in g.itens if i["resultado"] == "reprovado"]
    sem_ressalva = not any(i["resultado"] == "alerta" for i in g.itens) and not g.pendencias
    faixa = "nao_entregar" if reprovados else ("alta" if (not externa and sem_ressalva) else "mista")
    return {
        "schema_version": SCHEMA_VERSION, "gerado_em": _agora(), "modo": modo,
        "estado_tecnico": "bloqueado" if reprovados else "revisao_pronta",
        "gates": g.itens, "pendencias": g.pendencias, "documentos": documentos,
        **({"inventarios_pecas": contexto.vinculos(), "exigir_pecas": exigir_pecas} if contexto.ativo else {}),
        "artefatos": sorted(({"caminho": _rel(p, base), "tipo": t, "sha256": _sha(p)} for p, t in artefatos.items()),
                            key=lambda a: a["caminho"]),
        "tipo_entrega": tipo_entrega, "faixa": faixa,
        "aprovacao_humana_obrigatoria": externa or faixa != "alta",
        "revisao_humana": {"estado": "pendente"},
        "aviso": "revisao_pronta não é aprovação: libera a revisão humana; assinatura e protocolo dependem do revisor.",
    }


def _recalcular(qc: dict, base: Path):
    alterados, ausentes = [], []
    for a in qc["artefatos"]:
        p = (base / a["caminho"]) if not Path(a["caminho"]).is_absolute() else Path(a["caminho"])
        if not p.is_file():
            ausentes.append(a["caminho"])
        elif _sha(p) != a["sha256"]:
            alterados.append(a["caminho"])
    return alterados, ausentes


def aprovar(qc_path, revisor, registro, declaracao, decisao="aprovada", nota=None) -> dict:
    qcp = Path(qc_path).resolve()
    qc = json.loads(qcp.read_text(encoding="utf-8"))
    if not revisor or not revisor.strip():
        raise ValueError("revisor identificado é obrigatório")
    if not declaracao or not declaracao.strip():
        raise ValueError("a declaração do revisor é obrigatória")
    if decisao == "aprovada" and qc["estado_tecnico"] != "revisao_pronta":
        raise ValueError("o pacote está bloqueado na checagem técnica: não pode ser aprovado")
    alt, aus = _recalcular(qc, qcp.parent)
    if alt or aus:
        raise ValueError("o pacote mudou desde a auditoria (" + ", ".join(alt + aus) + "): rode 'auditar' de novo antes de decidir")
    return {"schema_version": SCHEMA_VERSION, "decisao": decisao,
            "revisor": {"nome": revisor.strip(), "registro": registro}, "declaracao": declaracao.strip(), "nota": nota,
            "registrado_em": _agora(), "qc_sha256": _sha(qcp), "artefatos": qc["artefatos"],
            "faixa": qc.get("faixa"), "tipo_entrega": qc.get("tipo_entrega")}


def _stdin_e_console() -> bool:
    """True só se o stdin é um terminal interativo de verdade.

    No Windows, `isatty()` devolve True para o dispositivo NUL (stdin nulo), então a checagem
    também pergunta ao sistema se o handle é um console (GetConsoleMode)."""
    if sys.stdin is None or not sys.stdin.isatty():
        return False
    if os.name == "nt":
        import ctypes
        import msvcrt

        try:
            modo = ctypes.c_uint32()
            h = ctypes.c_void_p(msvcrt.get_osfhandle(sys.stdin.fileno()))
            return bool(ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(modo)))
        except (OSError, ValueError, AttributeError):
            return False
    return True


def _exigir_terminal():
    if not _stdin_e_console():
        raise ValueError("a aprovação exige terminal interativo: a confirmação deve ser digitada pelo próprio revisor, "
                         "no painel de terminal. Agentes e scripts não podem registrá-la")


def _confirmar_no_terminal(qc_path, registro: dict) -> None:
    """Mostra o que será registrado e exige que a pessoa digite a frase de confirmação."""
    qc = json.loads(Path(qc_path).read_text(encoding="utf-8"))
    frase = ("APROVO " if registro["decisao"] == "aprovada" else "REPROVO ") + _sha(Path(qc_path))[:8]
    linhas = [
        f"Decisão:          {registro['decisao']}",
        f"Revisor:          {registro['revisor']['nome']} ({registro['revisor']['registro'] or 'sem registro informado'})",
        f"Declaração:       {registro['declaracao']}",
        f"Estado técnico:   {qc['estado_tecnico']}  |  pendências: {len(qc.get('pendencias', []))}",
        f"Artefatos ligados: {len(registro['artefatos'])} (qualquer mudança invalida esta decisão)",
        f"Para registrar, digite exatamente: {frase}",
        "> ",
    ]
    sys.stderr.write("\n".join(linhas))
    sys.stderr.flush()
    if sys.stdin.readline().strip() != frase:
        raise ValueError("a confirmação digitada não confere: nada foi registrado")


def status(qc_path, aprovacao_path=None) -> dict:
    qcp = Path(qc_path).resolve()
    qc = json.loads(qcp.read_text(encoding="utf-8"))
    obrig = qc.get("aprovacao_humana_obrigatoria", True)
    out = {"estado_tecnico": qc["estado_tecnico"], "faixa": qc.get("faixa"), "tipo_entrega": qc.get("tipo_entrega"),
           "aprovacao_humana_obrigatoria": obrig, "revisao_humana": "pendente", "alterados": [], "ausentes": [],
           "documentos": qc.get("documentos", {}), "pendencias": qc.get("pendencias", [])}
    # a integridade dos artefatos é conferida sempre, com ou sem aprovação: pacote mexido depois da auditoria não está liberado
    alt0, aus0 = _recalcular({"artefatos": qc.get("artefatos", [])}, qcp.parent)
    out.update(alterados=alt0, ausentes=aus0)
    out["liberado_para_uso"] = qc["estado_tecnico"] == "revisao_pronta" and not obrig and not (alt0 or aus0)
    if not aprovacao_path or not Path(aprovacao_path).is_file():
        return out
    ap = json.loads(Path(aprovacao_path).read_text(encoding="utf-8"))
    alt, aus = _recalcular({"artefatos": ap["artefatos"]}, qcp.parent)
    if _sha(qcp) != ap["qc_sha256"]:
        alt.append(qcp.name)
    # A aprovação antiga não pode apagar falhas encontradas no pacote atual.
    out.update(alterados=list(dict.fromkeys(alt0 + alt)), ausentes=list(dict.fromkeys(aus0 + aus)),
               revisor=ap["revisor"]["nome"], registrado_em=ap["registrado_em"])
    integro = not (out["alterados"] or out["ausentes"])
    out["revisao_humana"] = ap["decisao"] if integro else "invalidada"
    # A dispensa vale sem decisão registrada; nunca supera reprovação ou invalidação.
    out["liberado_para_uso"] = (qc["estado_tecnico"] == "revisao_pronta" and integro
                                and out["revisao_humana"] == "aprovada")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auditar")
    a.add_argument("--facts")
    a.add_argument("--claims")
    a.add_argument("--issues", help="apontamentos contratuais a validar, não apenas registrar por hash")
    a.add_argument("--campos", help="dados de preenchimento da minuta")
    a.add_argument("--modelo", help="modelo DOCX original; exige --campos e --minuta")
    a.add_argument("--minuta", help="minuta DOCX gerada; exige --campos e --modelo")
    a.add_argument("--regras", help="diretório dos pacotes de regras; padrão rules/br do projeto")
    a.add_argument("--pacote", default="servicos_saas,lgpd", help="pacotes usados na validação contratual")
    a.add_argument("--extracoes", action="append", default=[])
    a.add_argument("--modo", choices=("analise", "fundamentada"), default="fundamentada")
    a.add_argument("--artefato", action="append", default=[])
    a.add_argument("--timeline", help="timeline.json gerado por cronologia.py")
    a.add_argument("--matter", help="matter.json: confere conflitos de interesse e sigilo")
    a.add_argument("--tipo-entrega", choices=TIPOS_ENTREGA, required=True,
                   help="para quê o pacote será usado (obrigatório): cliente, peticao e contrato nunca ficam na faixa alta")
    a.add_argument("--reverificar", type=int, default=0, metavar="N", help="relê até N fontes oficiais e compara o texto")
    a.add_argument("--relatorio", action="append", default=[], help="relatório .md de entrega (precisa do aviso padrão)")
    a.add_argument("--sem-teses-centrais", action="store_true", help="declara que nenhuma proposição é tese central")
    a.add_argument("--saida", required=True)
    import pecas_uso
    pecas_uso.adicionar_argumentos(a)
    p = sub.add_parser("aprovar")
    p.add_argument("qc")
    p.add_argument("--revisor", required=True)
    p.add_argument("--registro")
    p.add_argument("--declaracao", required=True)
    p.add_argument("--decisao", choices=("aprovada", "reprovada"), default="aprovada")
    p.add_argument("--nota")
    p.add_argument("--saida", required=True)
    s = sub.add_parser("status")
    s.add_argument("qc")
    s.add_argument("aprovacao", nargs="?")
    n = ap.parse_args(argv)
    try:
        if n.cmd == "auditar":
            if not (n.facts or n.claims):
                raise ValueError("informe --facts e/ou --claims")
            qc = auditar(n.facts, n.claims, n.extracoes, n.modo, n.artefato, Path(n.saida).resolve().parent, n.timeline,
                         n.matter, n.tipo_entrega, n.reverificar, n.relatorio, n.sem_teses_centrais,
                         n.issues, n.campos, n.modelo, n.minuta, n.regras, n.pacote,
                         pecas=n.pecas, pecas_anteriores=n.pecas_anterior, exigir_pecas=n.exigir_pecas)
            Path(n.saida).write_text(json.dumps(qc, ensure_ascii=False, indent=2), encoding="utf-8")
            res, cod = qc, 0 if qc["estado_tecnico"] == "revisao_pronta" else 1
        elif n.cmd == "aprovar":
            _exigir_terminal()
            res = aprovar(n.qc, n.revisor, n.registro, n.declaracao, n.decisao, n.nota)
            _confirmar_no_terminal(n.qc, res)
            Path(n.saida).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
            cod = 0
        else:
            res = status(n.qc, n.aprovacao)
            cod = 0 if res["revisao_humana"] in ("aprovada", "pendente") else 1
    except (ValueError, OSError) as e:
        res, cod = {"erro": f"{type(e).__name__}: {e}"}, 1
    sys.stdout.buffer.write((json.dumps(res, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return cod


if __name__ == "__main__":
    sys.exit(main())
