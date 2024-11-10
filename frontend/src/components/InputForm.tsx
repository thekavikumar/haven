'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { z } from 'zod';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { useClerk } from '@clerk/nextjs';
import { LocateIcon } from 'lucide-react';
import axios from 'axios';
import { Slider } from './ui/slider';
import { Textarea } from './ui/textarea';
import { Checkbox } from './ui/checkbox';

const contactMethods = ['Phone', 'Email', 'Text message', 'In-person'];

const FormSchema = z.object({
  name: z.string().min(2, {
    message: 'Username must be at least 2 characters.',
  }),
  phone: z.string().min(10, {
    message: 'Phone number must be at least 10 characters.',
  }),
  location: z.object({
    lat: z.number(),
    lng: z.number(),
  }),
  occurrenceDuration: z
    .string()
    .min(1, { message: 'Please specify a duration.' }),
  frequency: z.string().min(1, { message: 'Please specify a frequency.' }),
  visibleInjuries: z.enum(['Yes', 'No']),
  preferredContact: z
    .array(z.enum(['Phone', 'Email', 'Text message', 'In-person']))
    .min(1, {
      message: 'Please select at least one contact method.',
    }),
  currentSituation: z
    .string()
    .min(5, { message: 'Please describe the current situation.' }),
  culprit: z.string().min(5, { message: 'Please describe the culprit.' }),
});

// interface InputFormProps {
//   setResImage: (resImage: string) => void;
// }
// { setResImage }: InputFormProps
export function InputForm({ setText }: { setText: (resText: string) => void }) {
  const { user } = useClerk();

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      name: user?.fullName || '',
      phone: '',
      location: { lat: 0, lng: 0 }, // Default to zero coordinates
      occurrenceDuration: '',
      frequency: '',
      visibleInjuries: 'No',
      preferredContact: [],
      currentSituation: '',
      culprit: '',
    },
  });

  const [occurrenceDuration, setOccurrenceDuration] = useState(1);
  const [frequency, setFrequency] = useState(1);

  const getUserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          // Set the location as an object with lat and lng
          form.setValue('location', { lat: latitude, lng: longitude });
        },
        (error) => {
          console.error('Error fetching location:', error);
        }
      );
    } else {
      console.error('Geolocation is not supported by this browser.');
    }
  };

  async function onSubmit(data: z.infer<typeof FormSchema>) {
    try {
      const res = await axios.post('/api/generate-text', data);
      // setResImage(res.data.url);
      // console.log('Image generated:', res.data.url);
      console.log('Text generated:', res.data.text);
      setText(res.data.text);
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="max-w-2xl mx-auto space-y-6 w-full"
      >
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Your name" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="phone"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Phone</FormLabel>
              <FormControl>
                <Input placeholder="Your phone number" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="location"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Location</FormLabel>
              <FormControl>
                <Input
                  placeholder="Type or auto-detect your location"
                  value={`Lat: ${field.value.lat}, Lon: ${field.value.lng}`}
                  readOnly
                />
              </FormControl>
              <Button
                type="button"
                onClick={getUserLocation}
                className="mt-2 flex items-center gap-2"
                variant={'outline'}
              >
                <LocateIcon className="h-5 w-5" />
                Auto-detect Location
              </Button>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="occurrenceDuration"
          render={({ field }) => (
            <FormItem>
              <FormLabel>How long has it been occurring</FormLabel>
              <FormControl>
                <div className="flex items-center gap-2">
                  <Slider
                    {...field}
                    value={[occurrenceDuration]}
                    min={1}
                    max={100}
                    onValueChange={(value) => {
                      setOccurrenceDuration(value[0]);
                      field.onChange(value[0]);
                    }}
                  />
                  <span>{occurrenceDuration}</span>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="frequency"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Frequency of Incidents</FormLabel>
              <FormControl>
                <div className="flex items-center gap-2">
                  <Slider
                    {...field}
                    value={[frequency]}
                    min={1}
                    max={100}
                    onValueChange={(value) => {
                      setFrequency(value[0]);
                      field.onChange(value[0]);
                    }}
                  />
                  <span>{frequency}</span>
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="preferredContact"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Preferred Contact Method</FormLabel>
              <FormControl>
                <div className="space-y-2">
                  {contactMethods.map((method) => (
                    <div key={method} className="flex items-center gap-2">
                      <Checkbox
                        checked={field.value.includes(
                          method as
                            | 'Phone'
                            | 'Email'
                            | 'Text message'
                            | 'In-person'
                        )}
                        onCheckedChange={(checked) => {
                          const newValue = checked
                            ? [...field.value, method]
                            : field.value.filter((item) => item !== method);
                          field.onChange(newValue);
                        }}
                      />
                      <span>{method}</span>
                    </div>
                  ))}
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="currentSituation"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Describe the Current Situation</FormLabel>
              <FormControl>
                <Textarea placeholder="Describe the situation" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="culprit"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Describe the Culprit</FormLabel>
              <FormControl>
                <Textarea placeholder="Who is responsible" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit">Generate Text</Button>
      </form>
    </Form>
  );
}
