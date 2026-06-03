"""
BMW E46 M57 Fault Code Knowledge Base
=======================================
Since there is no scrapable BMW-equivalent to the Ross-Tech Wiki,
this script creates a curated knowledge base of the most common
BMW E46 330d (M57 engine) fault codes and diagnostic information.

Data is compiled from community knowledge (E46Fanatics, Bimmerfest,
BMW service documentation) and covers the DDE4 engine management
system and common chassis/body faults.

Author: Person A — Data Engineer
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASETS_DIR = os.path.join(PROJECT_ROOT, "datasets")
CORPUS_FILE = os.path.join(DATASETS_DIR, "bmw_fault_corpus.json")


# ---------------------------------------------------------------------------
# BMW E46 330d M57 — Common Fault Codes & Diagnostic Knowledge
# ---------------------------------------------------------------------------
# The M57D30 engine uses the Bosch DDE4 (EDC15) engine management system.
# BMW uses both standard P-codes (via OBD-II port) and proprietary hex codes
# (via BMW-specific diagnostic tools like INPA/ISTA).
# This database focuses on the P-code equivalents for OBD-II compatibility.
# ---------------------------------------------------------------------------

BMW_FAULT_DATABASE = [
    {
        "code": "P0380",
        "title": "Glow Plug/Heater Circuit A Malfunction",
        "symptoms": [
            "Difficult cold starting, especially in winter",
            "Extended cranking time before engine fires",
            "Glow plug warning light stays on or flashes",
            "White/blue smoke on cold start",
            "Rough idle for first few minutes after cold start"
        ],
        "causes": [
            "Failed glow plug(s) — common on M57 engines after 100,000 km",
            "Faulty glow plug control module (relay)",
            "Corroded glow plug wiring connectors",
            "Poor ground connection at engine block",
            "Glow plug tip swollen/seized in cylinder head (common on high-mileage M57)"
        ],
        "solutions": [
            "Test each glow plug individually with a multimeter — resistance should be 0.5-1.0 ohms",
            "Check glow plug relay operation — should click when ignition is turned to position 2",
            "Inspect wiring harness connector at each glow plug for corrosion or heat damage",
            "If glow plugs are seized, apply penetrating oil and allow to soak before removal",
            "BMW recommends replacing all 6 glow plugs simultaneously — use Beru GE100 or equivalent",
            "Torque specification for M57 glow plugs: 15 Nm (11 ft-lb)"
        ],
        "notes": "The M57 engine has 6 glow plugs (one per cylinder). A single failed plug may not trigger the code — multiple plug failures are common. Always check the glow plug control module fuse (F36 in the E46 fuse box) before replacing plugs."
    },
    {
        "code": "P0100",
        "title": "Mass Air Flow (MAF) Sensor Circuit Malfunction",
        "symptoms": [
            "Loss of power, especially under acceleration",
            "Poor throttle response and turbo lag",
            "Black smoke from exhaust",
            "Increased fuel consumption",
            "Engine enters limp mode (reduced power)",
            "Rough or unstable idle"
        ],
        "causes": [
            "Contaminated MAF sensor element (oil or dirt buildup)",
            "Damaged MAF sensor hot-film element",
            "Air leaks in intake tract between MAF and turbo inlet",
            "Cracked or split intake boot/intercooler hoses",
            "Faulty MAF sensor wiring or connector (corroded pins)",
            "Failed MAF sensor — common failure on M57 after 80,000 km"
        ],
        "solutions": [
            "Clean MAF sensor with dedicated MAF cleaner spray (do NOT use carb cleaner or contact cleaner)",
            "Inspect all intake hoses from air filter box to intercooler for cracks, splits, or loose clamps",
            "Check MAF connector for bent or corroded pins — apply dielectric grease after cleaning",
            "If cleaning does not resolve, replace MAF sensor — BMW part number 13627788744 or Bosch equivalent",
            "After replacement, clear fault codes and perform a throttle adaptation reset via diagnostic software",
            "Check for intake manifold swirl flap issues which can affect MAF readings on M57 engines"
        ],
        "notes": "The M57 MAF sensor is located in the air filter housing. When replacing, ensure the new sensor arrow points in the direction of airflow. A faulty MAF can cause the DDE to miscalculate fuel injection quantities, leading to excessive smoke and poor performance."
    },
    {
        "code": "P0401",
        "title": "Exhaust Gas Recirculation (EGR) Insufficient Flow",
        "symptoms": [
            "Check engine light illuminated",
            "Rough idle, especially when warm",
            "Loss of power at low RPM",
            "Increased NOx emissions",
            "Slight engine knock or pinging under load",
            "Poor fuel economy"
        ],
        "causes": [
            "Carbon buildup blocking EGR valve — extremely common on diesel M57 engines",
            "EGR valve diaphragm failure (stuck closed)",
            "Blocked or restricted EGR cooler passages",
            "Vacuum hose leak or crack to EGR valve actuator",
            "EGR position sensor malfunction",
            "Intake manifold heavily carbonized (restricting EGR flow path)"
        ],
        "solutions": [
            "Remove and clean EGR valve — soak in carb cleaner to dissolve carbon deposits",
            "Inspect EGR cooler for blockage — coolant passage should flow freely",
            "Check vacuum lines to EGR actuator for cracks or leaks — replace as needed",
            "If EGR valve is mechanically damaged, replace — BMW part number 11717804381",
            "Clean intake manifold ports and swirl flap area to restore airflow",
            "Consider EGR blanking plate as a temporary diagnostic measure (note: may not be road-legal)",
            "After repair, perform EGR adaptation reset via INPA/ISTA diagnostic software"
        ],
        "notes": "The M57 engine's EGR system is known for heavy carbon buildup due to diesel combustion byproducts. Short trips and city driving accelerate this. BMW recommends periodic EGR cleaning every 60,000 km. When cleaning the EGR valve, also inspect the intake manifold swirl flaps which can seize or break."
    },
    {
        "code": "P0235",
        "title": "Turbocharger Boost Sensor A Circuit Malfunction",
        "symptoms": [
            "Loss of boost pressure — reduced power/acceleration",
            "Engine enters limp mode",
            "Turbo whistle changes pitch or disappears",
            "Excessive black smoke under load",
            "Boost gauge (if fitted) reads lower than normal"
        ],
        "causes": [
            "Failed boost pressure sensor (MAP sensor on intake manifold)",
            "Corroded or damaged sensor connector/wiring",
            "Vacuum/boost leak in intercooler hoses or intake tract",
            "Faulty turbocharger wastegate actuator (sticking or seized)",
            "Split intercooler end tank (common E46 failure point)",
            "VNT actuator linkage binding or broken (variable nozzle turbo)"
        ],
        "solutions": [
            "Check boost pressure sensor connector for corrosion — clean and apply dielectric grease",
            "Test sensor with multimeter — should read approximately 1.0V at atmospheric pressure",
            "Pressure test the entire boost system: intercooler, hoses, and connections",
            "Inspect turbo VNT mechanism for free movement — actuator rod should move smoothly",
            "Check intercooler for cracks or split end tanks — common failure at 100,000+ km",
            "If turbo wastegate is sticking, the actuator can often be rebuilt rather than replacing the entire turbo",
            "Replace boost sensor if faulty — BMW part number 13617787140"
        ],
        "notes": "The M57D30 in the E46 330d uses a Garrett GT2256V variable geometry turbocharger. The VNT mechanism can stick due to carbon buildup from the EGR system. Regular highway driving helps keep the VNT mechanism clean. If boost control issues persist, check the vacuum system that controls the VNT actuator."
    },
    {
        "code": "P0093",
        "title": "Fuel System Leak Detected — Large Leak",
        "symptoms": [
            "Engine cranks but will not start or starts and immediately stalls",
            "Loss of fuel rail pressure",
            "Diesel fuel smell around engine bay",
            "Rough running and misfiring on all cylinders",
            "Engine loses power intermittently, then recovers"
        ],
        "causes": [
            "Cracked or damaged fuel injector return line (plastic lines on M57 are prone to cracking)",
            "Failed fuel pressure regulator on common rail",
            "Leaking injector seal or copper washer",
            "Damaged high-pressure fuel pump (CP1 or CP3)",
            "Cracked fuel rail",
            "Fuel filter housing seal leak",
            "Fuel line connections loose or corroded"
        ],
        "solutions": [
            "Inspect all fuel injector return lines — the plastic return lines on the M57 become brittle with age and are the most common cause",
            "Replace all injector return lines as a set — BMW part number 13537787537 (set)",
            "Check copper injector sealing washers — replace if flattened or corroded",
            "Inspect fuel pressure regulator for external leaks",
            "Check fuel rail pressure with diagnostic tool — should hold 250-300 bar at idle, 1350+ bar under load",
            "Inspect fuel filter housing O-ring seal — replace if swollen or damaged",
            "Use a fuel pressure gauge to isolate the leak location systematically"
        ],
        "notes": "The M57 common rail system operates at extremely high pressure (up to 1350 bar). NEVER attempt to loosen high-pressure fuel lines while the engine is running. The plastic fuel injector return lines are the #1 failure point and should be replaced as preventive maintenance on any M57 with over 100,000 km."
    },
    {
        "code": "P0299",
        "title": "Turbocharger/Supercharger Underboost Condition",
        "symptoms": [
            "Noticeable power loss, especially during acceleration",
            "Engine enters limp mode (power reduced warning)",
            "Slow turbo spool-up / excessive turbo lag",
            "Maximum speed limited to approximately 100 km/h in limp mode",
            "Possible whistling or hissing noise from engine bay"
        ],
        "causes": [
            "Boost leak in intercooler piping, hoses, or clamps",
            "Turbocharger VNT mechanism sticking (carbon buildup)",
            "Torn or split turbo intake hose",
            "Wastegate actuator vacuum line disconnected or cracked",
            "Worn turbocharger shaft bearings (excessive play)",
            "EGR system fault causing exhaust gas recirculation issues",
            "Blocked catalytic converter or DPF creating excessive exhaust backpressure"
        ],
        "solutions": [
            "Perform a boost leak test on the entire intake and intercooler system — pressurize to 1.5 bar and listen for leaks",
            "Remove and inspect turbocharger VNT actuator linkage — should move freely through full range",
            "Clean VNT mechanism if accessible — use appropriate diesel-safe solvents",
            "Check all intercooler hoses and clamps — tighten or replace as needed",
            "Inspect turbo for shaft play: lateral play should not exceed 0.05mm, axial play should not exceed 0.10mm",
            "If turbo bearings are worn, turbo rebuild or replacement is required",
            "Check exhaust backpressure — excessive pressure indicates blocked DPF or catalytic converter"
        ],
        "notes": "Underboost on the M57 is frequently caused by the VNT mechanism sticking in the open position due to carbon deposits from the EGR system. An Italian tune-up (sustained high-RPM driving) can sometimes temporarily free a sticking VNT. For a permanent fix, the turbo may need to be removed for VNT cleaning or the actuator may need replacement."
    },
    {
        "code": "P0335",
        "title": "Crankshaft Position Sensor A Circuit Malfunction",
        "symptoms": [
            "Engine cranks but does not start",
            "Intermittent stalling while driving",
            "Rough running and misfiring",
            "Tachometer fluctuates or drops to zero intermittently",
            "Loss of power with possible limp mode activation"
        ],
        "causes": [
            "Failed crankshaft position sensor (CKP sensor) — common failure on M57 after 120,000+ km",
            "Damaged sensor wiring harness (heat damage from proximity to exhaust)",
            "Corroded CKP sensor connector",
            "Excessive gap between sensor and reluctor ring on flywheel/flexplate",
            "Cracked or damaged reluctor ring teeth",
            "Oil contamination on sensor tip"
        ],
        "solutions": [
            "The CKP sensor on the M57 is located on the lower rear of the engine block, near the flywheel",
            "Remove and inspect the sensor tip for metal debris, oil contamination, or physical damage",
            "Check sensor resistance — should measure 800-1400 ohms at room temperature",
            "Inspect wiring harness for heat damage — the exhaust proximity can melt insulation",
            "Replace sensor — BMW part number 13627789098 or Bosch equivalent",
            "Ensure correct installation gap — sensor should sit flush against the mounting surface",
            "After replacement, clear codes and test start. No adaptation needed for CKP sensor."
        ],
        "notes": "A failing CKP sensor on the M57 often exhibits intermittent symptoms — the engine may run fine for days, then suddenly stall or refuse to start. This is because the sensor can be heat-sensitive, failing only when hot. If intermittent no-start is experienced, try cooling the sensor area with water or compressed air — if the engine then starts, the CKP sensor is confirmed faulty."
    },
    {
        "code": "P0171",
        "title": "System Too Lean — Bank 1",
        "symptoms": [
            "Rough idle",
            "Hesitation during acceleration",
            "Increased fuel consumption",
            "Black or white exhaust smoke",
            "Engine misfiring under load"
        ],
        "causes": [
            "Vacuum leak in intake manifold or associated hoses",
            "Faulty MAF sensor reading incorrect air mass",
            "Clogged fuel filter restricting fuel delivery",
            "Weak fuel pump unable to maintain rail pressure",
            "Leaking fuel injector(s)",
            "EGR valve stuck open (excess exhaust gas diluting intake charge)",
            "Cracked intake manifold (common on plastic intake manifolds)"
        ],
        "solutions": [
            "Check for intake/vacuum leaks using smoke testing or carb cleaner spray method",
            "Inspect and test MAF sensor — clean or replace if faulty",
            "Replace fuel filter — BMW recommends every 30,000 km for diesel engines",
            "Check fuel rail pressure with diagnostic tool — should be 250-300 bar at idle",
            "Test injector return quantities — maximum 50ml per minute at idle per injector",
            "Inspect EGR valve operation — clean or replace as needed",
            "Check intake manifold for cracks, especially around the swirl flap area"
        ],
        "notes": "On the M57 diesel engine, 'System Too Lean' typically relates to air-fuel ratio issues detected by the lambda sensor. Unlike petrol engines, diesel lean conditions are often caused by insufficient fuel delivery rather than excess air. Always check fuel system components first."
    },
    {
        "code": "P0420",
        "title": "Catalyst System Efficiency Below Threshold — Bank 1",
        "symptoms": [
            "Check engine light (MIL) illuminated",
            "Slight sulphur/rotten egg smell from exhaust",
            "Reduced engine performance in some cases",
            "May fail emissions testing",
            "Usually no drivability symptoms in early stages"
        ],
        "causes": [
            "Catalytic converter substrate degraded or contaminated",
            "Oil burning entering exhaust system (worn valve stem seals or piston rings)",
            "Use of incorrect or contaminated fuel",
            "Exhaust leaks before the catalytic converter (false readings)",
            "Failed downstream oxygen/lambda sensor giving false efficiency readings",
            "Engine misfiring causing unburned fuel to damage catalyst",
            "DPF regeneration issues causing excessive exhaust temperatures"
        ],
        "solutions": [
            "First verify the fault — check both upstream and downstream lambda sensor operation with live data",
            "Inspect exhaust system for leaks between engine and catalytic converter",
            "Test downstream lambda sensor separately — replace if it shows no switching activity",
            "If catalyst is confirmed failed, replacement is required",
            "BMW OEM catalytic converter part number varies by production date — consult ETK",
            "After replacement, clear codes and perform at least 3 complete drive cycles for readiness monitors",
            "Address root cause (oil burning, misfires) before replacing catalyst to prevent repeat failure"
        ],
        "notes": "On the M57 diesel, this code is less common than on petrol engines. When it does appear, it is often caused by downstream sensor degradation rather than actual catalyst failure. Always verify sensor operation before condemning the catalytic converter. The E46 330d uses a close-coupled pre-catalyst followed by a main underfloor catalyst."
    },
    {
        "code": "P0480",
        "title": "Cooling Fan 1 Control Circuit Malfunction",
        "symptoms": [
            "Engine overheating, especially in traffic or at low speeds",
            "Cooling fan does not activate or runs constantly",
            "A/C system underperforming (condenser fan shared with engine cooling)",
            "Coolant temperature warning on dashboard",
            "Automatic transmission may overheat (shared cooling circuit)"
        ],
        "causes": [
            "Failed auxiliary cooling fan motor — common E46 failure due to brush wear",
            "Blown fan relay or fuse",
            "Faulty fan control module (final stage resistor)",
            "Coolant temperature sensor sending incorrect signal to DDE",
            "Damaged wiring to fan motor connector",
            "Failed fan clutch (on viscous-coupled main fan, if equipped)"
        ],
        "solutions": [
            "Check fan fuse in engine bay fuse box — replace if blown",
            "Test fan motor directly with 12V supply — motor should spin freely",
            "Inspect fan relay in fuse box — swap with identical relay to test",
            "Check coolant temperature sensor readings with diagnostic tool — should match actual temp",
            "Inspect wiring to fan motor for corrosion or damage, especially at the connector",
            "Replace auxiliary fan motor — BMW part number 64546988913",
            "If viscous fan clutch is faulty, replace — BMW part number 11527505302",
            "Always replace the fan clutch with the water pump during preventive maintenance"
        ],
        "notes": "The E46 cooling system is notoriously problematic. When addressing this code, it is strongly recommended to inspect the entire cooling system: expansion tank (cracks common), water pump (plastic impeller failure), thermostat (sticking open/closed), and all coolant hoses. BMW recommends replacing the expansion tank, thermostat, and water pump together as preventive maintenance at 100,000 km."
    },
    {
        "code": "P0128",
        "title": "Coolant Thermostat — Coolant Temperature Below Thermostat Regulating Temperature",
        "symptoms": [
            "Engine takes excessively long to reach operating temperature",
            "Heater output is poor or lukewarm",
            "Fuel consumption increased (engine running in cold enrichment mode too long)",
            "Temperature gauge stays below normal operating range",
            "DPF regeneration may not complete properly"
        ],
        "causes": [
            "Thermostat stuck in the open position — very common on E46 after 80,000 km",
            "Coolant temperature sensor reading inaccurately",
            "Thermostat housing cracked or leaking (allows coolant bypass)",
            "Air trapped in cooling system preventing proper thermostat operation",
            "Wrong thermostat specification installed (incorrect opening temperature)"
        ],
        "solutions": [
            "Replace thermostat — the E46 M57 uses a map-controlled thermostat (electrically heated)",
            "BMW part number 11537509227 for M57 thermostat assembly",
            "When replacing, also replace the thermostat housing O-ring and gasket",
            "Bleed the cooling system thoroughly after replacement — E46 is notoriously difficult to bleed",
            "Use BMW's bleeder screw on top of the thermostat housing to purge air",
            "Verify coolant temperature sensor accuracy after thermostat replacement",
            "Normal operating temperature for the M57 should be 90-105°C depending on load"
        ],
        "notes": "The M57's map-controlled thermostat is electrically heated by the DDE to optimize warm-up time and operating temperature based on driving conditions. Unlike a traditional wax thermostat, failure of the electrical heating element can also cause this code. Always use an OEM-specification thermostat — aftermarket units with incorrect opening temperatures will cause ongoing issues."
    },
    {
        "code": "P0201",
        "title": "Injector Circuit Malfunction — Cylinder 1",
        "symptoms": [
            "Engine misfiring on one cylinder",
            "Rough idle with noticeable vibration",
            "Loss of power — engine running on 5 cylinders",
            "Knocking or diesel clatter from affected cylinder",
            "Excessive smoke (white or black depending on failure mode)"
        ],
        "causes": [
            "Failed fuel injector — common rail piezo injector failure on M57",
            "Injector wiring harness damaged or corroded",
            "Injector connector pin corrosion or poor contact",
            "DDE (engine ECU) injector driver circuit failure",
            "Injector coding lost in ECU (requires recoding after replacement)"
        ],
        "solutions": [
            "Read injector correction values (IMA values) with diagnostic tool — values exceeding ±3 mg/stroke indicate a failing injector",
            "Perform an injector back-leak test — maximum 50ml per minute at idle (700 RPM)",
            "Check injector wiring harness — inspect for heat damage, oil contamination, or frayed wires",
            "Test injector resistance — should measure 0.3-1.0 ohms depending on type",
            "If injector replacement is needed, always replace the copper sealing washer and hold-down bolt",
            "Injector torque specification: 9 Nm for the hold-down bolt (M57)",
            "After replacement, the new injector correction code (IMA) must be programmed into the DDE via ISTA/INPA",
            "BMW part number for M57 injectors varies by production date — verify via last 7 digits of VIN"
        ],
        "notes": "The M57 uses Bosch common rail piezo injectors. These injectors have an IMA (injector trim) correction value printed on each injector body. This 6-digit code MUST be programmed into the DDE after any injector replacement — failure to do so will cause rough running, incorrect fueling, and potential DPF issues. This code (P0201) is for Cylinder 1; P0202-P0206 indicate Cylinders 2-6 respectively."
    },
    {
        "code": "P0116",
        "title": "Engine Coolant Temperature Circuit Range/Performance",
        "symptoms": [
            "Inaccurate temperature gauge readings",
            "Engine fan running at incorrect times (too early or too late)",
            "Poor heater performance",
            "Engine management light illuminated",
            "Cold start issues — incorrect fueling based on wrong temperature reading"
        ],
        "causes": [
            "Failed coolant temperature sensor (CTS) — common age-related failure",
            "Corroded CTS connector (exposed to coolant leaks and engine bay moisture)",
            "Wiring fault between CTS and DDE module",
            "Low coolant level causing sensor to read air instead of coolant",
            "Air pocket trapped around the sensor location"
        ],
        "solutions": [
            "Locate the CTS — on the M57, it is on the cylinder head near the thermostat housing",
            "Check coolant level first — low level can cause erratic sensor readings",
            "Read live data with diagnostic tool — compare CTS reading vs. actual temperature (infrared thermometer)",
            "Inspect connector for green/white corrosion — clean with electrical contact cleaner",
            "Test sensor resistance: approximately 2.5 kΩ at 20°C, 300Ω at 80°C",
            "Replace CTS — BMW part number 13621433077",
            "Top off and bleed cooling system after any work near the thermostat area"
        ],
        "notes": "The M57 has two coolant temperature sensors — one for the gauge cluster and one for the DDE engine management. This P-code refers to the DDE sensor. If only the gauge is reading incorrectly but the engine runs fine, the gauge sensor (different part) may be at fault instead."
    },
    {
        "code": "P2002",
        "title": "Diesel Particulate Filter Efficiency Below Threshold — Bank 1",
        "symptoms": [
            "DPF warning light illuminated on dashboard",
            "Reduced engine power / limp mode",
            "Increased exhaust smoke",
            "Strong exhaust smell",
            "Frequent attempted regeneration cycles (higher idle RPM, cooling fan running at standstill)",
            "Fuel economy significantly worsened"
        ],
        "causes": [
            "DPF fully loaded with soot beyond regeneration capacity",
            "Failed DPF pressure differential sensor",
            "Exhaust temperature sensor fault preventing regeneration",
            "Frequent short journeys preventing passive regeneration from completing",
            "Faulty injector(s) causing incomplete combustion and excessive soot",
            "EGR system fault increasing soot production",
            "DPF substrate cracked or melted from excessive regeneration temperatures"
        ],
        "solutions": [
            "Read DPF soot loading level with diagnostic tool — if below 45g, a forced regeneration may clear it",
            "Perform forced regeneration via INPA/ISTA (engine must be at operating temperature, vehicle stationary)",
            "If forced regeneration fails, professional DPF cleaning (chemical flush or thermal cleaning) may be required",
            "Check DPF differential pressure sensor — should read 0 mbar with engine off, rising with soot load",
            "Inspect all exhaust temperature sensors — the M57 has sensors before and after the DPF",
            "Address root cause of excessive soot: injectors, EGR, MAF, turbo condition",
            "If DPF is physically damaged (cracked substrate), replacement is required",
            "BMW part number for E46 330d DPF varies — consult dealer with VIN"
        ],
        "notes": "Not all E46 330d models were equipped with a DPF — it depends on the production date and market. Pre-2004 EU3 models typically do not have a DPF. If your vehicle has a DPF, regular highway driving (30+ minutes at 2500+ RPM) is essential for passive regeneration. Vehicles used exclusively for short city trips will inevitably accumulate excessive soot."
    }
]


def build_corpus_chunks() -> list:
    """Build corpus chunks from the BMW fault database."""
    chunks = []

    for fault in BMW_FAULT_DATABASE:
        # Build a detailed, readable content block
        lines = []
        lines.append(f"BMW E46 330d (M57 Engine) — Fault Code {fault['code']}: {fault['title']}")
        lines.append("")

        lines.append("Possible Symptoms:")
        for symptom in fault['symptoms']:
            lines.append(f"• {symptom}")
        lines.append("")

        lines.append("Possible Causes:")
        for cause in fault['causes']:
            lines.append(f"• {cause}")
        lines.append("")

        lines.append("Diagnostic and Repair Procedure:")
        for i, step in enumerate(fault['solutions'], 1):
            lines.append(f"{i}. {step}")
        lines.append("")

        if fault.get('notes'):
            lines.append(f"Technical Note: {fault['notes']}")

        content = "\n".join(lines)

        chunk = {
            "content": content,
            "metadata": {
                "make": "BMW",
                "model": "E46 330d",
                "year_range": "1999-2005",
                "source_file": "bmw_e46_m57_knowledge_base",
                "page_number": None,
                "section": f"{fault['code']} - {fault['title']}"
            }
        }
        chunks.append(chunk)

    return chunks


def main():
    print("=" * 60)
    print("BMW E46 M57 — Fault Code Knowledge Base Generator")
    print("=" * 60)

    chunks = build_corpus_chunks()

    print(f"\nGenerated {len(chunks)} fault code chunks")

    # Save corpus
    print(f"Saving to: {CORPUS_FILE}")
    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    # Summary
    word_counts = [len(c["content"].split()) for c in chunks]
    avg_words = sum(word_counts) / len(word_counts) if word_counts else 0

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Chunks created:  {len(chunks)}")
    print(f"  Avg chunk size:  {avg_words:.0f} words")
    print(f"  Min chunk size:  {min(word_counts)} words")
    print(f"  Max chunk size:  {max(word_counts)} words")
    print(f"  Codes covered:   {', '.join(f['code'] for f in BMW_FAULT_DATABASE)}")
    print(f"  Output file:     {CORPUS_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
