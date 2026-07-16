export const meta = {
  name: 'cftr-cis-partner-correction',
  description: 'Re-extract CIS-only partners for the 177 complex-allele hits and reaffirm verdicts',
  phases: [{ title: 'CisFix', detail: 'one agent per batch of ~15 hits' }],
}
const _a = (typeof args === 'string') ? JSON.parse(args) : args
const N = (_a && _a.numBatches) ? _a.numBatches : 12

const SCHEMA = {
  type:'object', additionalProperties:false, required:['results'],
  properties:{ results:{ type:'array', items:{
    type:'object', additionalProperties:false,
    required:['sp_id','verdict','cis_partners','trans_partners','reason'],
    properties:{
      sp_id:{type:'integer'},
      verdict:{type:'string', enum:['yes','uncertain','no']},
      cis_partners:{ type:'array', items:{
        type:'object', additionalProperties:false, required:['as_written','best_hgvs_or_name'],
        properties:{
          as_written:{type:'string', description:'partner exactly as written in the source text'},
          best_hgvs_or_name:{type:'string', description:'the partner as a resolvable identifier: prefer a modern cDNA (c.####X>Y) or legacy nucleotide (e.g. 3791C>T) or standard name (F508del, R117H). If you cannot map it, repeat the raw form.'}
        }
      }, description:'ONLY variants that are IN CIS / on the SAME allele as the primary variant. Empty if none are confirmed cis.' },
      trans_partners:{ type:'array', items:{type:'string'}, description:'variants explicitly on the OTHER allele / in trans (for audit; do NOT include these in cis_partners)' },
      reason:{type:'string'}
    }
  }}}
}

const INSTR = (path)=> `You are a CFTR curator FIXING the partner assignment for candidate COMPLEX ALLELES from CFTR1 (genet.sickkids).

A complex allele = the primary variant PLUS one or more other CFTR variant(s) on the SAME chromosome / same allele / IN CIS. A variant on the OTHER allele / other chromosome / in trans (typical compound-heterozygous partner such as a ΔF508 on the other allele) is NOT part of the complex allele.

Read intermediate/batches3/${path} — JSON array of hit records: sp_id, primary_cdna, primary_protein, primary_legacy, current_verdict, other_details, phenotype.

For EACH record, decide:
1. verdict: "yes" (a second variant is explicitly in cis/same allele/same chromosome as the primary), "uncertain" (a second variant co-occurs but cis vs trans is NOT stated — e.g. "in conjunction with X", "associated with X" with no phase given), or "no" (all co-mentioned variants are explicitly trans / on the other allele, or there is no real second CFTR variant). Correct the current_verdict if it is wrong. IMPORTANT: unstated phase => "uncertain", never "yes".
2. cis_partners: list ONLY the variant(s) genuinely in cis with the primary. For each give as_written (verbatim from text) and best_hgvs_or_name (a resolvable identifier — modern cDNA like c.1647T>G, or legacy nucleotide like 3791C>T, or a standard name like F508del/R117H). If the primary_cdna ALREADY encodes the full complex allele by itself (e.g. it is written as c.[change1;change2]), return an EMPTY cis_partners list and set verdict per the text — the primary name already contains both changes.
3. trans_partners: any variant explicitly on the other allele / in trans (audit only).

Key rules:
- ΔF508 / F508del "on the other allele/chromosome" is TRANS — put it in trans_partners, NOT cis_partners.
- Watch for the inference case: if the text says the primary + variant X are found in a patient who has ΔF508 "on the other allele", then primary + X are together in cis (cis_partners = [X]); ΔF508 is trans.
- Poly-T (5T/7T/9T) or TG-repeat tracts stated in cis DO count as cis partners; give best_hgvs_or_name like "c.1210-12T[5]" for 5T when applicable, else the raw form.
- Return EVERY record in the batch.`

phase('CisFix')
const paths=Array.from({length:N},(_,i)=>`b3_${String(i).padStart(2,'0')}.json`)
const results=await parallel(paths.map(bp=>()=>
  agent(INSTR(bp),{label:`cisfix:${bp}`,phase:'CisFix',schema:SCHEMA,agentType:'general-purpose'})
    .then(r=>(r&&r.results)||[]).catch(()=>[])
))
const all=[]; for(const r of results){ if(r) all.push(...r) }
log(`cis-fix collected ${all.length} corrected hit records`)
return { total: all.length, results: all }
