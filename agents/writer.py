import os
from state import ADRState

def writer(state: ADRState) -> ADRState:
    draft_adrs = state["draft_adrs"]
    
    os.makedirs("adr_output", exist_ok=True)
    
    final_adrs = []
    
    for i, adr_text in enumerate(draft_adrs):
        # extract theme from first line "# ADR: Theme Name"
        # first line looks like "# ADR: Performance optimization"
        first_line = adr_text.split("\n")[0]        # "# ADR: Performance optimization"
        theme = first_line.replace("# ADR: ", "")   # "Performance optimization"
        
        # create clean filename — lowercase, spaces to dashes
        safe_name = theme.lower().replace(" ", "-")
        filename = f"adr_output/{i+1:03d}-{safe_name}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(adr_text)
        
        final_adrs.append(filename)
        print(f"  Saved: {filename}")
    
    return {
        "final_adrs": final_adrs
    }