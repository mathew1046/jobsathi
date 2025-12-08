import asm_Beng from './asm_Beng.json'
import ben_Beng from './ben_Beng.json'
import brx_Deva from './brx_Deva.json'
import doi_Deva from './doi_Deva.json'
import gom_Deva from './gom_Deva.json'
import guj_Gujr from './guj_Gujr.json'
import hin_Deva from './hin_Deva.json'
import kan_Knda from './kan_Knda.json'
import kas_Arab from './kas_Arab.json'
import kas_Deva from './kas_Deva.json'
import mai_Deva from './mai_Deva.json'
import mal_Mlym from './mal_Mlym.json'
import mar_Deva from './mar_Deva.json'
import mni_Beng from './mni_Beng.json'
import mni_Mtei from './mni_Mtei.json'
import npi_Deva from './npi_Deva.json'
import ory_Orya from './ory_Orya.json'
import pan_Guru from './pan_Guru.json'
import san_Deva from './san_Deva.json'
import sat_Olck from './sat_Olck.json'
import snd_Arab from './snd_Arab.json'
import snd_Deva from './snd_Deva.json'
import tam_Taml from './tam_Taml.json'
import tel_Telu from './tel_Telu.json'
import urd_Arab from './urd_Arab.json'

// Map UI language codes to bundled translation JSON files
// English will be handled separately using ui_strings.json
const LANG_MAP = {
  en: null,
  as: asm_Beng,
  bn: ben_Beng,
  brx: brx_Deva,
  doi: doi_Deva,
  gom: gom_Deva,
  gu: guj_Gujr,
  hi: hin_Deva,
  kn: kan_Knda,
  ks: kas_Arab,
  'ks-deva': kas_Deva,
  mai: mai_Deva,
  ml: mal_Mlym,
  mr: mar_Deva,
  mni: mni_Beng,
  'mni-mtei': mni_Mtei,
  npi: npi_Deva,
  or: ory_Orya,
  pa: pan_Guru,
  sa: san_Deva,
  sat: sat_Olck,
  sd: snd_Arab,
  'sd-deva': snd_Deva,
  ta: tam_Taml,
  te: tel_Telu,
  ur: urd_Arab,
}

export default LANG_MAP
