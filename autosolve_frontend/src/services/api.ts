import type { DiagnosticRequest, DiagnosticResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000';

// High-fidelity mock responses for Demo Mock Mode
const MOCK_RESPONSES: Record<string, DiagnosticResponse> = {
  'volkswagen_golf_p0420': {
    problem_elaboration: 'The engine control module (ECM) monitors the efficiency of the catalytic converter system. When it detects that the catalytic converter is not performing as efficiently as required (often due to aging catalyst substrate, exhaust leaks, or engine misfires leading to raw fuel entering the exhaust), it sets the diagnostic trouble code P0420. In this case, the efficiency has dropped below the minimum allowable threshold for exhaust emission control.',
    core_cause: 'Degraded catalytic converter substrate (internal catalyst breakdown).\nExhaust leak upstream of or near the catalytic converter.\nFaulty post-catalyst oxygen sensor (sensor 2) or wiring.\nUnburned fuel entering the catalyst from engine misfires (faulty spark plugs or ignition coils).',
    solution: '1. Inspect for exhaust leaks: Examine all flanges, welds, and flex joints upstream of the catalytic converter. Repair any leaks found immediately.\n2. Perform a sensor check: Verify proper switching operation of the upstream (Sensor 1) and downstream (Sensor 2) oxygen sensors using a live-data scan tool. If Sensor 2 mimics Sensor 1\'s wave, the catalyst is defective.\n3. Verify engine health: Repair any active ignition misfire codes (e.g., P0300-P0304) or fuel trim codes (P0171/P0172) before replacing the catalytic converter to prevent destroying a new unit.\n4. Replace the catalytic converter assembly if diagnostic checks confirm catalyst failure. Clear the diagnostic trouble codes and perform a drive cycle verification.',
    sources: [
      'VW Golf Service Manual — Page 142 (Exhaust Systems)',
      'Technical Service Bulletin TSB 20-04-12 — Page 3 (Catalyst Efficiency Diagnostics)',
      'Ross-Tech VAG Diagnostics Wiki — Page 9 (Fault Code P0420)'
    ],
    confidence_score: 0.94,
    is_fallback: false
  },
  'toyota_corolla_p0171': {
    problem_elaboration: 'The OBD-II code P0171 indicates that the fuel injection system has reached its rich limit while trying to correct an overly lean air-fuel ratio. This means the engine control module (ECM) is detecting too much air and/or too little fuel entering the combustion chambers, causing it to add up to 25% or more fuel trim to compensate.',
    core_cause: 'Vacuum leaks downstream of the Mass Air Flow (MAF) sensor (e.g., torn intake boot, leaking intake manifold gasket).\nDirty or faulty Mass Air Flow (MAF) sensor.\nWeak fuel pump, clogged fuel filter, or failing fuel pressure regulator.\nClogged fuel injector(s) or leaking exhaust system upstream of the O2 sensor.',
    solution: '1. Inspect intake tract: Visually inspect all vacuum hoses, the intake boot, and PCV valves for cracks or leaks. Spray intake cleaner around the intake manifold gasket while monitoring short-term fuel trims.\n2. Clean the MAF sensor: Carefully clean the MAF hot wire elements using dedicated MAF sensor cleaner spray. Reinstall and verify air flow grams/second (g/s) reading at idle.\n3. Test fuel pressure: Connect a fuel pressure gauge to the fuel rail and verify pressure is within the specified 44-50 psi range under load.\n4. Replace the front oxygen sensor (Sensor 1) if it is sluggish or unresponsive during snap-throttle tests.',
    sources: [
      'Toyota Corolla 2014-2018 Workshop Manual — Page 85 (Fuel & Emissions)',
      'Technical Service Bulletin TSB 17-08-01 — Page 2 (MAF Sensor Cleaning & Calibration)'
    ],
    confidence_score: 0.88,
    is_fallback: false
  },
  'bmw_3-series_oil leak': {
    problem_elaboration: 'Oil leaks on the BMW N20/N52/N55 engines are highly common and typically result from degraded elastomer seals subject to high thermal cycling. If oil is dripping onto the hot exhaust manifold, it will create a distinct burning smell and visible smoke in the engine bay, posing a mild fire hazard and accelerating engine bay wire harness degradation.',
    core_cause: 'Cracked or warped plastic Valve Cover / Valve Cover Gasket (VCG).\nFailed Oil Filter Housing Gasket (OFHG) leaking down the front of the block.\nHardened Oil Pan Gasket (OPG) leaking oil from the lower block seal.',
    solution: '1. Clean and dye test: Clean the engine block using degreaser. Add UV dye to the engine oil, run the engine for 15 minutes, and inspect using a UV light to trace the highest point of oil seepage.\n2. Replace Oil Filter Housing Gaskets: If leaking, replace both the filter-to-housing and housing-to-block profile gaskets. Flush spilled coolant/oil to prevent damage to the drive belt (which can shred and be sucked through the front crank seal).\n3. Replace Valve Cover & Gasket: Due to plastic warping, always replace the entire plastic valve cover assembly along with the gasket if mileage exceeds 80,000 miles.\n4. Replace Oil Pan Gasket: If leaking, support the engine from above, lower the front subframe, remove the oil pan, clean all mating surfaces, and install a new gasket with fresh aluminum bolts (torque to yield).',
    sources: [
      'BMW 3-Series Workshop Manual — Page 112 (Cylinder Head Cover)',
      'BMW Technical Service Bulletin TSB 11-04-13 — Page 1 (Oil Filter Housing Seal Upgrades)'
    ],
    confidence_score: 0.91,
    is_fallback: false
  }
};

const FALLBACK_RESPONSE: DiagnosticResponse = {
  problem_elaboration: 'No relevant documentation was found for this vehicle and fault combination.',
  core_cause: 'Could not be determined — no verified documentation found.',
  solution: 'Please consult a certified technician or the official workshop manual for your specific vehicle.',
  sources: [],
  confidence_score: 0.0,
  is_fallback: true
};

export async function diagnose(request: DiagnosticRequest, isMockMode: boolean): Promise<DiagnosticResponse> {
  if (isMockMode) {
    // Artificial delay to simulate network latency & LLM generation
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const key = `${request.make.toLowerCase()}_${request.model.toLowerCase()}_${request.query.toLowerCase()}`;
    
    // Exact key search
    if (MOCK_RESPONSES[key]) {
      return MOCK_RESPONSES[key];
    }
    
    // Fuzzy search matching parts of query
    const match = Object.keys(MOCK_RESPONSES).find(mockKey => {
      const [mMake, mModel, mQuery] = mockKey.split('_');
      const makeMatch = request.make.toLowerCase().includes(mMake) || mMake.includes(request.make.toLowerCase());
      const modelMatch = request.model.toLowerCase().includes(mModel) || mModel.includes(request.model.toLowerCase());
      const queryMatch = request.query.toLowerCase().includes(mQuery) || mQuery.includes(request.query.toLowerCase());
      return makeMatch && modelMatch && queryMatch;
    });

    if (match) {
      return MOCK_RESPONSES[match];
    }

    // Default mock behavior if code looks standard but not match (e.g. Golf with another OBD-II code)
    if (request.make.toLowerCase() === 'volkswagen' && request.query.toUpperCase().startsWith('P')) {
      return MOCK_RESPONSES['volkswagen_golf_p0420'];
    }

    return FALLBACK_RESPONSE;
  }

  // Live API Mode
  try {
    const response = await fetch(`${API_BASE_URL}/diagnose`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    return await response.json();
  } catch (error: any) {
    console.error('API Error:', error);
    throw new Error(error.message || 'Failed to connect to the diagnostic server.');
  }
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) return false;
    const data = await response.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
}
