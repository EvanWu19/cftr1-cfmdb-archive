export const meta = {
  name: 'cftr-complex-allele-pass2',
  description: 'Second AI pass over non-keyword CFTR1 variants to catch hidden complex alleles',
  phases: [{ title: 'Judge2', detail: 'one agent per batch of ~20 non-keyword variants' }],
}

const _a = (typeof args === 'string') ? JSON.parse(args) : args
const N = (_a && _a.numBatches) ? _a.numBatches : 81

const SCHEMA = {
  type: 'object', additionalProperties: false, required: ['judgements'],
  properties: { judgements: { type: 'array', items: {
    type: 'object', additionalProperties: false,
    required: ['sp_id','is_complex_allele','confidence','keyword','text_referring_to','reason','partner_tokens'],
    properties: {
      sp_id: { type: 'integer' },
      is_complex_allele: { type: 'string', enum: ['yes','no','uncertain'] },
      confidence: { type: 'string', enum: ['high','medium','low'] },
      keyword: { type: 'string' },
      text_referring_to: { type: 'string' },
      reason: { type: 'string' },
      partner_tokens: { type: 'array', items: { type: 'string' } }
    } } } }
}

const INSTR = (path) => `You are a CFTR molecular-genetics curator doing a SECOND-PASS safety screen of the CFTR1 (genet.sickkids) database for COMPLEX ALLELES.

A "complex allele" (cis-compound / same-allele) = a variant reported to occur TOGETHER WITH one or more OTHER CFTR variant(s) on the SAME chromosome / same allele / in cis. A patient being a compound heterozygote (two variants on OPPOSITE alleles / in trans) is NOT a complex allele.

IMPORTANT CONTEXT: The records in this batch already FAILED an automated keyword screen (they do NOT contain obvious triggers like "in cis", "same chromosome", "together with", "also carries", "haplotype", "complex", "and <MUT>", "second mutation", etc.). Your job is to catch any HIDDEN complex allele that the keyword screen missed. Realistically MOST records here will be "no" — only flag "yes"/"uncertain" when the text genuinely describes a second CFTR variant on the SAME allele/chromosome/in cis.

Read intermediate/batches2/${path} — a JSON array of variant records (sp_id, cdna_name, protein_name, legacy_name, other_details, phenotype).

For EACH record:
- "yes": text (or the variant name itself) genuinely indicates a second CFTR variant in cis / same allele / same chromosome / bundled into one allele, even if worded unusually.
- "uncertain": a second variant co-occurs but cis vs trans is not stated.
- "no": no second CFTR variant, OR the second variant is clearly in trans / on the other allele / a separate patient, OR only marker-haplotype/repeat background with no cis sequence variant. This will be the majority.

partner_tokens: every identifier for the co-occurring partner variant(s) exactly as written (protein like R117H, legacy nucleotide like 3791C/T, cDNA, or name like F508del). Empty if none.
keyword: the phrase that made you flag it, or "none".
text_referring_to: the exact clause establishing the relationship, or empty string.

Return ALL records from the batch (including every "no").`

phase('Judge2')
const paths = Array.from({length: N}, (_,i)=> `b2_${String(i).padStart(2,'0')}.json`)
const results = await parallel(paths.map((bp)=> ()=>
  agent(INSTR(bp), { label: `judge2:${bp}`, phase: 'Judge2', schema: SCHEMA, agentType: 'general-purpose' })
    .then(r => ({ batch: bp, judgements: (r && r.judgements) || [] }))
    .catch(()=> ({ batch: bp, judgements: [] }))
))
const all = []
for (const r of results) { if (r && r.judgements) all.push(...r.judgements) }
log(`pass2 collected ${all.length} judgements from ${results.filter(Boolean).length}/${N} batches`)
return { total: all.length, judgements: all }
