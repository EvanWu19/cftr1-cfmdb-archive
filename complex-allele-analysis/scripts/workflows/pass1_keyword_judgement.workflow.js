export const meta = {
  name: 'cftr-complex-allele-screen',
  description: 'Classify CFTR1 candidate variants as complex alleles and extract partner tokens',
  phases: [{ title: 'Judge', detail: 'one agent per batch of ~12 candidates' }],
}

const _a = (typeof args === 'string') ? JSON.parse(args) : args
const N = (_a && _a.numBatches) ? _a.numBatches : 31
const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['judgements'],
  properties: {
    judgements: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['sp_id','is_complex_allele','confidence','keyword','text_referring_to','reason','partner_tokens'],
        properties: {
          sp_id: { type: 'integer' },
          is_complex_allele: { type: 'string', enum: ['yes','no','uncertain'] },
          confidence: { type: 'string', enum: ['high','medium','low'] },
          keyword: { type: 'string', description: 'the specific word/phrase in the text that signals a complex allele, or "none"' },
          text_referring_to: { type: 'string', description: 'the exact sentence/snippet from Other Details or Submitted Phenotype Details that refers to the co-occurring variant; empty string if none' },
          reason: { type: 'string', description: 'concise judgement reasoning' },
          partner_tokens: { type: 'array', items: { type: 'string' }, description: 'every identifier for the co-occurring partner variant(s) exactly as written in the text (e.g. K1220E, 3791C/T, R117H, F508del). Empty if none.' }
        }
      }
    }
  }
}

const INSTR = (path) => `You are a CFTR molecular-genetics curator screening variants from the CFTR1 (genet.sickkids) database for COMPLEX ALLELES.

A "complex allele" (a.k.a. cis-compound / same-allele) is when a variant is reported to occur TOGETHER WITH one or more OTHER CFTR variant(s) on the SAME chromosome / same allele / in cis. This is different from a patient simply being a compound heterozygote (two variants on OPPOSITE alleles / in trans) — that is NOT a complex allele.

Read intermediate/batches/${path} — a JSON array of variant records. Each has: sp_id, cdna_name, protein_name, legacy_name, other_details, phenotype (Submitted Phenotype Details).

For EACH record decide is_complex_allele:
- "yes": text clearly states this variant is on the same allele / in cis / on the same chromosome / found together with another named variant, OR the variant name itself bundles a second change. Examples of YES language: "found together with K1220E on the same chromosome", "in cis with 3791C/T", "complex allele", "on the same allele as R117H", "always found with the 5T", "occurs in combination with".
- "no": the co-mentioned variant is on the OTHER allele / in trans / "on the other chromosome" / describes the second allele of a compound-heterozygous patient; or the keyword matched but context is unrelated (e.g. "complex phenotype", "haplotype background" with no cis partner, "also carries" referring to the trans allele).
- "uncertain": co-occurrence is mentioned but cis vs trans is genuinely ambiguous / not stated.

CRITICAL distinctions:
- "on the same chromosome / same allele / in cis / together with" => complex allele (yes).
- "on the other allele / other chromosome / in trans / compound heterozygous with" => NOT complex (no).
- Polymorphisms/backgrounds explicitly reported in cis (e.g. poly-T 5T/7T/9T, TG repeats, M470V) COUNT as complex-allele partners when stated in cis.

For partner_tokens: list EVERY way the partner variant is written in the text (protein like K1220E, legacy nucleotide like 3791C/T, cDNA, or common name like F508del). Include all of them so they can be resolved later. If multiple distinct partners, include all.

keyword: the single most relevant trigger phrase actually present in the text.
text_referring_to: copy the exact clause/sentence that establishes the relationship.

Return ALL records from the batch (do not skip any), including the "no" ones.`

phase('Judge')
const batchPaths = Array.from({length: N}, (_,i)=> `batch_${String(i).padStart(2,'0')}.json`)
const results = await parallel(batchPaths.map((bp,i)=> ()=>
  agent(INSTR(bp), { label: `judge:${bp}`, phase: 'Judge', schema: SCHEMA, agentType: 'general-purpose' })
    .then(r => ({ batch: bp, judgements: (r && r.judgements) || [] }))
))

const all = []
for (const r of results) { if (r && r.judgements) all.push(...r.judgements) }
log(`collected ${all.length} judgements from ${results.filter(Boolean).length}/${N} batches`)
return { total: all.length, judgements: all }
