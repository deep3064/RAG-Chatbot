import re

def smart_flatten():
    input_file = "data/my_notes.txt"
    output_file = "data/flattened_notes.txt"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    flattened_lines = []
    
    # Variables to hold context
    current_header = "System"
    current_name = "" 
    
    # Buffer to hold lines of a block until we find the Name
    block_buffer = []

    def flush_block(header, name, buffer):
        # Helper to write out the buffer with the Name attached
        prefix = f"{header}"
        if name: prefix += f" ({name})"
        
        for item in buffer:
            # Create the perfect line: "USER: u1002 (Bob Smith) | Currency: EUR"
            flattened_lines.append(f"{prefix} | {item}")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"): continue

        # 1. New Block Detected
        if line.startswith("["):
            # Flush the previous block
            if current_header and block_buffer:
                flush_block(current_header, current_name, block_buffer)
            
            # Reset for new block
            current_header = line.strip("[]")
            current_name = ""
            block_buffer = []
            continue

        # 2. Check if this line is the Name
        if line.startswith("Name:"):
            current_name = line.split("Name:")[1].strip()
        
        # 3. Check if this line is a Technician (for Smart City nodes)
        if "Technician:" in line and not current_name:
             current_name = line.split("Technician:")[1].strip()

        # Add line to buffer
        clean_line = line.replace("Enabled (true)", "Enabled").replace("Disabled (false)", "Disabled")
        block_buffer.append(clean_line)

    # Flush the last block
    if current_header and block_buffer:
        flush_block(current_header, current_name, block_buffer)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(flattened_lines))
    
    print(f"✅ Smart Data Created! Check data/flattened_notes.txt")
    print("--- Preview ---")
    for l in flattened_lines[:5]: print(l)

if __name__ == "__main__":
    smart_flatten()