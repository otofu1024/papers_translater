import { useRef, useState } from "react";

type DropzoneProps = {
  disabled?: boolean;
  onFileSelected: (file: File) => void;
};

export function Dropzone({ disabled, onFileSelected }: DropzoneProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }
    const file = files[0];
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      return;
    }
    onFileSelected(file);
  };

  return (
    <div
      className={`dropzone ${dragging ? "dragging" : ""} ${disabled ? "disabled" : ""}`}
      onDragEnter={(event) => {
        event.preventDefault();
        if (!disabled) {
          setDragging(true);
        }
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={(event) => {
        event.preventDefault();
        setDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        if (!disabled) {
          handleFiles(event.dataTransfer.files);
        }
      }}
      onClick={() => {
        if (!disabled) {
          inputRef.current?.click();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(event) => handleFiles(event.target.files)}
      />
      <p className="dropzone-title">Drop PDF Here</p>
      <p className="dropzone-caption">or click to choose file</p>
    </div>
  );
}

