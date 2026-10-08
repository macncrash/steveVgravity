# Blowball Station: pod structural check (step 2)

**Question:** will a 41 t, 20 m pod hold together on a 1.2 m stalk off the hub?

**Answer:** yes, but only after one design change. The analysis found that a flat root bulkhead bends like a
plate. A conical **flare** between stalk and pod fixes it, the way a dandelion stalk flares into its seed head.

## Model

- **STEVE part:** [Pod Structural Model](https://stevecad.studio/?document=eebcc9ab-8f60-4777-ac62-fae99679d451),
  revision 4. It is a single solid, cantilevered from the hub collar (`@z-` fixed).
- **Geometry:**
  - Stalk: Ø1.2 m tube, 20 mm wall.
  - Pod: Ø4.06 m × 20.3 m shell, 40 mm wall.
  - Bulkheads: 60 mm.
  - Flare: 1.3 m long, 30 mm wall.
- **Smeared idealisation:** each wall stands for skin + stringers + ring frames. The material is Al 2219-T87
  (E 73.1 GPa, ν 0.33, yield 393 MPa, typical), with its density set so the solid carries the full **41,275 kg**
  pod mass from [MASS_BUDGET.md](MASS_BUDGET.md): 3,296 kg/m³ with the flare, 3,398 kg/m³ without.
- **Half model:** symmetry about the X–Z plane (cut face held in y), with half the applied forces. The full model
  needed more than the 6 GB a STEVE solve may use at a 0.1 m mesh.
- **Load case:** a docking load at the pod tip (5 kN lateral + 15 kN axial, an assumed low-impact docking envelope,
  **EST**) plus a 0.05 m/s² lateral station acceleration on the whole pod. That acceleration is ~50× a typical ISS
  reboost, so it is conservative.

## Results (STEVE, 0.1 m quadratic tetrahedra)

| | Flat root bulkhead (rev 2) | **Flared joint (rev 4)** | Hand check (`pod_beam_check.py`) |
|---|---:|---:|---:|
| Peak von Mises | 77.3 MPa | **17.8 MPa** | 6.2 MPa (stalk root, beam bending only) |
| Max displacement | 136 mm | **25.6 mm** | 18.5 mm (rigid joint) |
| First bending mode | rejected by STEVE's eigen check (residual 3.5e-3 > 1e-3) | **0.623 Hz** | 0.653 Hz (−5 %) |
| Force / moment balance | 3.3e-9 / 9.9e-10 | 4.6e-9 / 1.4e-10 | |
| Body mass (half model) | 20,639 kg | 20,637 kg | 20,638 kg (½ × 41,275) |

Studies:
[static](https://stevecad.studio/?document=eebcc9ab-8f60-4777-ac62-fae99679d451&workspace=simulate&study=b2645039-60e9-4dbc-833c-b0cc130521c9&run=e37da749-2e3b-4806-a200-8775f43efd72) ·
[modal](https://stevecad.studio/?document=eebcc9ab-8f60-4777-ac62-fae99679d451&workspace=simulate&study=5303ae1e-ac6b-4eca-bb65-58bbcae07000&run=ccd3d3ce-ee72-41f0-af79-158e332e980e)

## Reading it

- **Why the flat bulkhead failed.** The pod's 133 kN·m docking moment has to pass through a 60 mm flat plate
  between the Ø1.2 m stalk and the Ø4.06 m shell. The result implies a joint stiffness of about 1.7×10⁷ N·m/rad,
  roughly 12× the plate's bending stiffness D = E·t³/12(1−ν²) ≈ 1.5 MN·m. That is plate bending, not beam bending,
  and it explains both the 7× disagreement with the rigid-joint hand check and the soft first mode that failed
  STEVE's validation.
- **With the flare** the cone carries the moment in membrane action:
  - Stress falls 4.3× and deflection 5.3×.
  - The first mode, 0.62 Hz, agrees with the beam hand check to 5 % and passes every solver check.
- **Margins:** yield 393 MPa ÷ 17.8 MPa ≈ 22. These are *smeared* wall stresses, though. The real skin is 3–4 mm,
  so skin stresses are several times higher, and **cabin pressure governs the skin**: hoop p·r/t = 51–64 MPa for
  a 4.0–3.2 mm skin (hand calculation). Docking and acceleration loads are small next to it.
- **Dynamics:** at 0.62 Hz the pod rocking mode sits ~50× above a typical station attitude-control bandwidth
  (~0.01 Hz, EST), so control interaction is unlikely. Docking-transient response still needs a dynamic analysis.

## Not modelled (never claimed)

- Skin buckling.
- Fatigue.
- Bolt preload: the flange needs ~24–82 bolts; see MASS_BUDGET.md.
- Launch loads in the bay (axial g's).
- Thermal stress.
- Docking dynamics.
- The real stiffened-skin layout.
