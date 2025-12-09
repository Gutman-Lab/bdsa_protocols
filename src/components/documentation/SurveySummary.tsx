import { Card } from 'bdsa-react-components'
import type { SurveySummary as SurveySummaryType } from '../../utils/manuscriptParser'
import './SurveySummary.css'

interface SurveySummaryProps {
  summary: SurveySummaryType
}

export default function SurveySummary({ summary }: SurveySummaryProps) {
  return (
    <div className="survey-summary">
      <div className="summary-header">
        <h2>{summary.title}</h2>
        <div className="summary-stats">
          <div className="stat">
            <span className="stat-label">Response Rate:</span>
            <span className="stat-value">{summary.responseRate}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Responding Centers:</span>
            <span className="stat-value">{summary.respondingCenters} / {summary.totalCenters}</span>
          </div>
        </div>
      </div>

      <section className="summary-section">
        <h3>Key Findings</h3>
        <ul className="findings-list">
          {summary.keyFindings.map((finding, index) => (
            <li key={index}>{finding}</li>
          ))}
        </ul>
      </section>

      <section className="summary-section">
        <h3>Staining Protocols</h3>
        <div className="protocols-grid">
          {summary.stainingProtocols.map((protocol, index) => (
            <Card key={index} className="protocol-card">
              <h4>{protocol.stainType}</h4>
              <div className="protocol-stats">
                <span className="protocol-frequency">
                  {protocol.frequency} / {protocol.totalCenters} centers ({protocol.percentage}%)
                </span>
              </div>
              <div className="protocol-regions">
                <strong>Regions:</strong>
                <ul>
                  {protocol.regions.slice(0, 5).map((region, i) => (
                    <li key={i}>{region}</li>
                  ))}
                  {protocol.regions.length > 5 && (
                    <li className="more-regions">
                      +{protocol.regions.length - 5} more regions
                    </li>
                  )}
                </ul>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="summary-section">
        <h3>Region Protocols</h3>
        <div className="regions-list">
          {summary.regionProtocols.map((region, index) => (
            <Card key={index} className="region-card">
              <div className="region-header">
                <h4>{region.region}</h4>
                <span className="region-frequency">
                  {region.frequency} / {region.totalCenters} centers
                </span>
              </div>
              <div className="region-stains">
                <strong>Stains:</strong> {region.stains.join(', ')}
              </div>
              {region.landmarks && region.landmarks.length > 0 && (
                <div className="region-landmarks">
                  <strong>Landmarks:</strong>
                  <ul>
                    {region.landmarks.map((landmark, i) => (
                      <li key={i}>{landmark}</li>
                    ))}
                  </ul>
                </div>
              )}
              {region.sectioningApproach && region.sectioningApproach.length > 0 && (
                <div className="region-sectioning">
                  <strong>Sectioning:</strong> {region.sectioningApproach.join(', ')}
                </div>
              )}
            </Card>
          ))}
        </div>
      </section>

      <section className="summary-section">
        <h3>Section Thickness</h3>
        <div className="thickness-info">
          <div className="thickness-stats">
            <div className="thickness-stat">
              <span className="thickness-label">Range:</span>
              <span className="thickness-value">{summary.sectionThickness.min}μm - {summary.sectionThickness.max}μm</span>
            </div>
            <div className="thickness-stat">
              <span className="thickness-label">Most Common:</span>
              <span className="thickness-value">{summary.sectionThickness.mostCommon}μm</span>
            </div>
          </div>
          <div className="thickness-distribution">
            <strong>Distribution:</strong>
            <ul>
              {summary.sectionThickness.distribution.map((dist, i) => (
                <li key={i}>
                  {dist.size}μm: {dist.count} centers
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="summary-section">
        <h3>Antibodies Used</h3>
        <div className="antibodies-grid">
          <Card className="antibody-card">
            <h4>Tau</h4>
            <ul>
              {summary.antibodies.tau.map((ab, i) => (
                <li key={i}>{ab}</li>
              ))}
            </ul>
          </Card>
          <Card className="antibody-card">
            <h4>Amyloid Beta</h4>
            <ul>
              {summary.antibodies.amyloidBeta.map((ab, i) => (
                <li key={i}>{ab}</li>
              ))}
            </ul>
          </Card>
          <Card className="antibody-card">
            <h4>Alpha-synuclein</h4>
            <ul>
              {summary.antibodies.alphaSynuclein.map((ab, i) => (
                <li key={i}>{ab}</li>
              ))}
            </ul>
          </Card>
          <Card className="antibody-card">
            <h4>TDP-43</h4>
            <ul>
              {summary.antibodies.tdp43.map((ab, i) => (
                <li key={i}>{ab}</li>
              ))}
            </ul>
          </Card>
        </div>
      </section>

      <section className="summary-section">
        <h3>Figures from Manuscript</h3>
        <div className="figures-grid">
          <Card className="figure-card">
            <img 
              src="/manuscript/images/figure-1765293494239-dcmrrfkiz.png" 
              alt="Figure 1: Heatmap showing number of centers using specific stains for different sampled regions"
            />
            <p><strong>Figure 1.</strong> Heatmap showing number of centers using specific stains for different sampled regions. The vertical axis displays the 19 regions surveyed and the horizontal axis displays the major stains surveyed.</p>
          </Card>
          <Card className="figure-card">
            <img 
              src="/manuscript/images/figure-1765293494248-fve381rzg.png" 
              alt="Figure 2: Bar plots showing the anatomical landmarks sampled in four brain regions"
            />
            <p><strong>Figure 2.</strong> Bar plots showing the anatomical landmarks sampled in four brain regions. The dashed line represents the total number of submitted surveys (38).</p>
          </Card>
          <Card className="figure-card">
            <img 
              src="/manuscript/images/figure-1765293494257-mz9icg9fu.png" 
              alt="Figure 3: Sectioning approaches for different brain regions"
            />
            <p><strong>Figure 3.</strong> For each region, the number of centers that sample the region via different sectioning approaches is shown using stacked bar plots.</p>
          </Card>
        </div>
      </section>
    </div>
  )
}

