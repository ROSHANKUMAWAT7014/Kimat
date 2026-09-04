import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  getStates,
  getDistricts,
  getCities,
  getLocalities,
} from "@/data/indiaLocations";

interface LocationData {
  state: string;
  district: string;
  city: string;
  locality: string;
}

interface Props {
  value: LocationData;
  onChange: (key: keyof LocationData, val: string) => void;
  onContinue: () => void;
}

function Combobox({
  options,
  value,
  onChange,
  placeholder,
  emptyText,
  disabled,
}: {
  options: string[];
  value: string;
  onChange: (val: string) => void;
  placeholder: string;
  emptyText: string;
  disabled?: boolean;
}) {
  const [open, setOpen] = React.useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className="w-full justify-between bg-surface"
        >
          {value ? value : <span className="text-muted-foreground">{placeholder}</span>}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
        <Command>
          <CommandInput placeholder={`Search...`} />
          <CommandList>
            <CommandEmpty>{emptyText}</CommandEmpty>
            <CommandGroup>
              {options.map((opt) => (
                <CommandItem
                  key={opt}
                  value={opt}
                  onSelect={(currentValue) => {
                    // CommandItem value is lowercased by default in cmdk unless specified,
                    // but we want the original case, so we use `opt` directly.
                    onChange(opt === value ? "" : opt);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn("mr-2 h-4 w-4", value === opt ? "opacity-100" : "opacity-0")}
                  />
                  {opt}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export function LocationSelector({ value, onChange, onContinue }: Props) {
  const states = React.useMemo(() => getStates(), []);
  const districts = React.useMemo(() => getDistricts(value.state), [value.state]);
  const cities = React.useMemo(
    () => getCities(value.state, value.district),
    [value.state, value.district],
  );
  const localities = React.useMemo(
    () => getLocalities(value.state, value.district, value.city),
    [value.state, value.district, value.city],
  );

  const handleStateChange = (state: string) => {
    onChange("state", state);
    onChange("district", "");
    onChange("city", "");
    onChange("locality", "");
  };

  const handleDistrictChange = (district: string) => {
    onChange("district", district);
    onChange("city", "");
    onChange("locality", "");
  };

  const handleCityChange = (city: string) => {
    onChange("city", city);
    onChange("locality", "");
  };

  const isComplete = value.state && value.district && value.city && value.locality;

  return (
    <div className="rounded-xl border border-border bg-surface/50 p-5 shadow-sm">
      <div className="mb-4">
        <h3 className="font-display text-lg font-semibold text-foreground">
          Select Property Location
        </h3>
        <p className="text-xs text-muted-foreground">
          Choose your location to get a more accurate property price estimate.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>State *</Label>
          <Combobox
            options={states}
            value={value.state}
            onChange={handleStateChange}
            placeholder="Search or select state"
            emptyText="No state found."
          />
        </div>

        <div className="space-y-2">
          <Label>District *</Label>
          <Combobox
            options={districts}
            value={value.district}
            onChange={handleDistrictChange}
            placeholder="Search or select district"
            emptyText="No district found."
            disabled={!value.state}
          />
        </div>

        <div className="space-y-2">
          <Label>City / Town *</Label>
          <Combobox
            options={cities}
            value={value.city}
            onChange={handleCityChange}
            placeholder="Search or select city"
            emptyText="No city found."
            disabled={!value.district}
          />
        </div>

        <div className="space-y-2">
          <Label>Area / Locality *</Label>
          <Combobox
            options={localities}
            value={value.locality}
            onChange={(val) => onChange("locality", val)}
            placeholder="Search or select locality"
            emptyText="No locality found."
            disabled={!value.city}
          />
        </div>

      </div>


      <div className="mt-6 flex justify-end">
        <Button onClick={onContinue} disabled={!isComplete} className="w-full sm:w-auto">
          Continue
        </Button>
      </div>
    </div>
  );
}
